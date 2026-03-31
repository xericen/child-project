import { OnInit, OnDestroy } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit, OnDestroy {
    serverName: string = '';
    serverId: string = '';

    // 디바이스/브라우저 감지
    isIOS: boolean = false;
    isAndroid: boolean = false;
    isPC: boolean = false;
    isSafari: boolean = false;
    isChrome: boolean = false;
    isSamsungInternet: boolean = false;
    isIOSChrome: boolean = false;
    isStandalone: boolean = false;

    // UI 상태
    showLoading: boolean = false;
    showDownloadButton: boolean = false;
    showFallbackGuide: boolean = false;

    // childcheck 상태 (부모 전용) - localStorage와 query param으로 유지
    private childcheckDone: boolean = false;

    private deferredPrompt: any = null;
    private promptHandler: any;
    private rejectCount: number = 0;

    constructor(public service: Service, public router: Router, private route: ActivatedRoute) {}

    public async ngOnInit() {
        await this.service.init();

        this.route.queryParams.subscribe(async (params) => {
            this.serverId = params['server_id'] || '';
            this.serverName = params['server_name'] || '';
            this.childcheckDone = params['childcheck_done'] === 'true';
            await this.service.render();
        });

        this.detectDevice();

        if (this.isStandalone) {
            await this.markInstalled();
            this.navigateNext();
            return;
        }

        this.setupPWA();
        await this.service.render();
    }

    ngOnDestroy() {
        if (this.promptHandler) {
            window.removeEventListener('beforeinstallprompt', this.promptHandler);
        }
    }

    private navigateNext() {
        // 첫 로그인에서는 childcheck_done=false로 들어오고, 재로그인은 저장 플래그로 note로 바로 이동한다.
        if (!this.childcheckDone) {
            this.router.navigate(['/childcheck']);
        } else {
            this.router.navigate(['/note']);
        }
    }

    private detectDevice() {
        const ua = navigator.userAgent;

        this.isStandalone = window.matchMedia('(display-mode: standalone)').matches
            || (window.navigator as any).standalone === true;

        this.isIOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
        this.isAndroid = /Android/i.test(ua);
        this.isPC = !this.isIOS && !this.isAndroid;

        this.isSamsungInternet = /SamsungBrowser/i.test(ua);
        this.isIOSChrome = this.isIOS && /CriOS/i.test(ua);
        this.isSafari = this.isIOS && /Safari/i.test(ua) && !/CriOS|FxiOS|OPiOS|EdgiOS/i.test(ua);
        this.isChrome = /Chrome/i.test(ua) && !/SamsungBrowser|Edg/i.test(ua) && !this.isIOS;
    }

    private setupPWA() {
        // index.pug의 글로벌 리스너가 미리 잡아둔 prompt 가져오기
        if ((window as any).__pwaInstallPrompt) {
            this.deferredPrompt = (window as any).__pwaInstallPrompt;
            delete (window as any).__pwaInstallPrompt;
        }

        // 이후 발생하는 prompt도 수신
        this.promptHandler = (e: any) => {
            e.preventDefault();
            this.deferredPrompt = e;
            // 로딩 중이었으면 다운로드 버튼으로 전환
            if (this.showLoading) {
                this.showLoading = false;
                this.showDownloadButton = true;
                this.service.render();
            }
        };
        window.addEventListener('beforeinstallprompt', this.promptHandler);

        // Android Chrome: prompt 여부에 따라 UI 분기
        if (this.isAndroid && this.isChrome) {
            if (this.deferredPrompt) {
                // prompt 이미 있음 → 바로 다운로드 버튼
                this.showDownloadButton = true;
            } else {
                // prompt 대기 → 로딩 표시
                this.showLoading = true;
                this.waitForPrompt();
            }
        }
    }

    private async waitForPrompt() {
        // SW 등록 완료 대기
        if ('serviceWorker' in navigator) {
            try { await navigator.serviceWorker.ready; } catch {}
        }

        // 대기 중 promptHandler에서 이미 전환됐으면 종료
        if (this.deferredPrompt) return;

        // 최대 5초 대기
        await new Promise<void>((resolve) => {
            if (this.deferredPrompt) { resolve(); return; }
            const onPrompt = (e: any) => {
                e.preventDefault();
                this.deferredPrompt = e;
                clearTimeout(timer);
                resolve();
            };
            const timer = setTimeout(() => {
                window.removeEventListener('beforeinstallprompt', onPrompt);
                resolve();
            }, 5000);
            window.addEventListener('beforeinstallprompt', onPrompt, { once: true });
        });

        // prompt 유무와 관계없이 다운로드 버튼 표시
        this.showLoading = false;
        this.showDownloadButton = true;
        await this.service.render();
    }

    public async onDownloadClick() {
        if (this.deferredPrompt) {
            // 유저 클릭 컨텍스트 → prompt() 정상 동작
            try {
                this.deferredPrompt.prompt();
                const result = await this.deferredPrompt.userChoice;
                this.deferredPrompt = null;

                if (result.outcome === 'accepted') {
                    this.navigateNext();
                    return;
                }

                // 거부 시
                this.rejectCount++;
                if (this.rejectCount >= 3) {
                    this.showDownloadButton = false;
                    this.showFallbackGuide = true;
                    await this.service.render();
                } else {
                    window.location.reload();
                }
            } catch {
                window.location.reload();
            }
        } else {
            // prompt 없음 → 새로고침으로 재시도
            window.location.reload();
        }
    }

    private async markInstalled() {
        try {
            await wiz.call("mark_installed");
        } catch {}
    }

    public async goToNote() {
        this.navigateNext();
    }

    get browserName(): string {
        if (this.isSamsungInternet) return '삼성 인터넷';
        if (this.isIOSChrome) return 'Chrome';
        if (this.isSafari) return 'Safari';
        if (this.isChrome) return 'Chrome';
        return '브라우저';
    }
}
