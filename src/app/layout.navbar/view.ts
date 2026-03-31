import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();
        await this.checkChildcheck();
        await this.service.render();
    }

    private async checkChildcheck() {
        try {
            const res = await wiz.call("check_childcheck");
            if (res.code === 200 && res.data?.need_childcheck === true) {
                this.router.navigate(['/childcheck']);
            }
        } catch (e) {}
    }
}
