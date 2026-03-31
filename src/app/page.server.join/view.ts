import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    serverCode: string = '';
    errorMessage: string = '';
    serverInfo: any = null;

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();
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

    public goBack() {
        this.router.navigate(['/']);
    }
}
