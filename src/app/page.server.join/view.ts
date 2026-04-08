import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    serverCode: string = '';
    errorMessage: string = '';
    serverInfo: any = null;
    savedServers: any[] = [];

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();
        this.loadSavedServers();
        await this.service.render();
    }

    private loadSavedServers() {
        try {
            const raw = localStorage.getItem('child_joined_servers');
            if (raw) this.savedServers = JSON.parse(raw);
        } catch {
            this.savedServers = [];
        }
    }

    private saveServer(server: any) {
        const existing = this.savedServers.filter((s: any) => s.id !== server.id);
        existing.unshift({ id: server.id, name: server.name, code: server.code || this.serverCode.toUpperCase() });
        this.savedServers = existing.slice(0, 10);
        localStorage.setItem('child_joined_servers', JSON.stringify(this.savedServers));
    }

    public async removeSavedServer(event: Event, index: number) {
        event.stopPropagation();
        this.savedServers.splice(index, 1);
        localStorage.setItem('child_joined_servers', JSON.stringify(this.savedServers));
        await this.service.render();
    }

    public async onInput() {
        await this.service.render();
    }

    public async verifyCode() {
        if (this.serverCode.length === 0) {
            this.errorMessage = '서버 회원번호를 입력해주세요.';
            await this.service.render();
            return;
        }

        this.errorMessage = '';
        const res = await wiz.call("verify_server_code", { server_code: this.serverCode });

        if (res.code === 200) {
            this.serverInfo = res.data;
            this.saveServer({ id: res.data.id, name: res.data.name, code: this.serverCode.toUpperCase() });
            this.router.navigate(['/main'], {
                queryParams: {
                    server_id: res.data.id,
                    server_name: res.data.name
                }
            });
        } else {
            this.errorMessage = res.data?.message || '유효하지 않은 서버 코드입니다.';
            await this.service.render();
        }
    }

    public async joinSavedServer(server: any) {
        const res = await wiz.call("verify_server_code", { server_code: server.code });
        if (res.code === 200) {
            this.saveServer({ id: res.data.id, name: res.data.name, code: server.code });
            this.router.navigate(['/main'], {
                queryParams: {
                    server_id: res.data.id,
                    server_name: res.data.name
                }
            });
        } else {
            this.savedServers = this.savedServers.filter((s: any) => s.id !== server.id);
            localStorage.setItem('child_joined_servers', JSON.stringify(this.savedServers));
            this.errorMessage = '해당 서버가 더 이상 유효하지 않습니다.';
            await this.service.render();
        }
    }

    public goBack() {
        this.router.navigate(['/']);
    }
}
