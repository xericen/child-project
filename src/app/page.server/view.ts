import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    isLoading: boolean = true;

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();

        // 자동 로그인 정보와 서버 정보가 있으면 바로 로그인 페이지로 이동
        const autoLogin = localStorage.getItem('child_auto_login');
        const serverInfo = localStorage.getItem('child_server_info');
        if (autoLogin && serverInfo) {
            try {
                const server = JSON.parse(serverInfo);
                if (server.server_id) {
                    this.router.navigate(['/main'], {
                        queryParams: { server_id: server.server_id, server_name: server.server_name }
                    });
                    return;
                }
            } catch {}
        }

        this.isLoading = false;
        await this.service.render();
    }

    public goCreate() {
        this.router.navigate(['/server/create']);
    }

    public goJoin() {
        this.router.navigate(['/server/join']);
    }
}
