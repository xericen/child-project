import { OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {

    email: string = '';
    password: string = '';
    serverName: string = '';
    rememberMe: boolean = false;
    isLoading: boolean = true;

    constructor(
        public service: Service,
        public router: Router,
        public route: ActivatedRoute
    ) { }

    public async ngOnInit() {
        await this.service.init();

        const params: any = {};
        const serverId = this.route.snapshot.queryParams['server_id'];
        const serverName = this.route.snapshot.queryParams['server_name'];
        if (serverId) params.server_id = serverId;
        if (serverName) params.server_name = serverName;

        const res = await wiz.call("get_server_info", params);
        if (res.code === 200) {
            this.serverName = res.data.server_name || '';
        } else {
            this.router.navigate(['/']);
            return;
        }

        // 자동 로그인 시도 — 성공하면 이 함수 안에서 navigate하고 return true
        const autoLoginDone = await this.tryAutoLogin();
        if (autoLoginDone) return;

        this.isLoading = false;
        await this.service.render();
    }

    private isStandalone(): boolean {
        return window.matchMedia('(display-mode: standalone)').matches
            || (window.navigator as any).standalone === true;
    }

    private async navigateAfterLogin(role: string, hasCompletedAllergyCheck: boolean, appInstalled: boolean) {
        // Standalone: 앱 설치 완료 처리
        if (this.isStandalone()) {
            await wiz.call("mark_installed");
            appInstalled = true;
        }

        // 첫 로그인: 앱 설치가 안 된 경우 install로 먼저 이동한다.
        if (!appInstalled) {
            const queryParams: any = {};
            queryParams.childcheck_done = (role === 'parent' && !hasCompletedAllergyCheck) ? 'false' : 'true';
            this.router.navigate(['/install'], { queryParams });
            return;
        }

        // 재로그인: 저장된 hasCompletedAllergyCheck가 true면 childcheck를 건너뛴다.
        if (role === 'parent' && !hasCompletedAllergyCheck) {
            this.router.navigate(['/childcheck']);
            return;
        }

        // Step 3: 노트 페이지
        await this.subscribePush();
        this.router.navigate(['/note']);
    }

    private async subscribePush() {
        try {
            if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
            const permission = await Notification.requestPermission();
            if (permission !== 'granted') return;
            const reg = await navigator.serviceWorker.ready;
            const res = await wiz.call("get_vapid_key");
            if (res.code !== 200) return;
            const publicKey = res.data.public_key;
            const applicationServerKey = this.urlBase64ToUint8Array(publicKey);
            let sub = await reg.pushManager.getSubscription();
            if (!sub) {
                sub = await reg.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: applicationServerKey
                });
            }
            const subJson = sub.toJSON();
            const ua = navigator.userAgent;
            let deviceType = 'pc';
            if (/Android/i.test(ua)) deviceType = 'android';
            else if (/iPad|iPhone|iPod/i.test(ua)) deviceType = 'ios';
            await wiz.call("subscribe_push", {
                endpoint: subJson.endpoint,
                p256dh: subJson.keys.p256dh,
                auth: subJson.keys.auth,
                device_type: deviceType
            });
        } catch (e) {
            console.log('Push subscription failed:', e);
        }
    }

    private urlBase64ToUint8Array(base64String: string): Uint8Array {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    private saveServerInfo() {
        const serverId = this.route.snapshot.queryParams['server_id'];
        const serverName = this.route.snapshot.queryParams['server_name'] || this.serverName;
        if (serverId) {
            localStorage.setItem('child_server_info', JSON.stringify({
                server_id: serverId,
                server_name: serverName
            }));
        }
    }

    private async tryAutoLogin(): Promise<boolean> {
        const saved = localStorage.getItem('child_auto_login');
        if (!saved) return false;

        try {
            const cred = JSON.parse(saved);
            if (cred.email && cred.password) {
                const res = await wiz.call("login", {
                    email: cred.email,
                    password: cred.password
                });
                if (res.code === 200) {
                    this.saveServerInfo();
                    const role = res.data?.role || 'parent';
                    const hasCompletedAllergyCheck = res.data?.hasCompletedAllergyCheck ?? res.data?.childcheck_done ?? false;
                    const appInstalled = res.data?.app_installed || false;
                    localStorage.setItem('hasCompletedAllergyCheck', hasCompletedAllergyCheck ? 'true' : 'false');
                    await this.navigateAfterLogin(role, hasCompletedAllergyCheck, appInstalled);
                    return true;
                } else {
                    localStorage.removeItem('child_auto_login');
                    localStorage.removeItem('child_server_info');
                    localStorage.removeItem('hasCompletedAllergyCheck');
                }
            }
        } catch {
            localStorage.removeItem('child_auto_login');
            localStorage.removeItem('child_server_info');
            localStorage.removeItem('hasCompletedAllergyCheck');
        }
        return false;
    }

    public async onLogin() {
        const res = await wiz.call("login", {
            email: this.email,
            password: this.password
        });

        if (res.code === 200) {
            if (this.rememberMe) {
                localStorage.setItem('child_auto_login', JSON.stringify({
                    email: this.email,
                    password: this.password
                }));
            } else {
                localStorage.removeItem('child_auto_login');
            }
            this.saveServerInfo();

            alert('로그인 되었습니다.');
            const role = res.data?.role || 'parent';
            const hasCompletedAllergyCheck = res.data?.hasCompletedAllergyCheck ?? res.data?.childcheck_done ?? false;
            const appInstalled = res.data?.app_installed || false;
            localStorage.setItem('hasCompletedAllergyCheck', hasCompletedAllergyCheck ? 'true' : 'false');
            await this.navigateAfterLogin(role, hasCompletedAllergyCheck, appInstalled);
        } else {
            alert(res.data?.message || '로그인 실패');
        }
        await this.service.render();
    }

    public goSignup() {
        this.router.navigate(['/signup']);
    }

    public goServer() {
        this.router.navigate(['/']);
    }

    public goServerCreate() {
        this.router.navigate(['/server/create']);
    }
}
