import { OnInit } from '@angular/core';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    public contacts: any[] = [];
    public loading: boolean = true;

    constructor(public service: Service) { }

    public async ngOnInit() {
        await this.service.init();
        await this.loadContacts();
        await this.service.render();
    }

    public async loadContacts() {
        this.loading = true;
        try {
            const res = await wiz.call("get_contacts");
            if (res.code === 200) {
                this.contacts = res.data.contacts || [];
            }
        } catch (e) { }
        this.loading = false;
    }

    public goBack() {
        history.back();
    }

    public callPhone(phone: string) {
        if (phone) {
            window.location.href = 'tel:' + phone;
        }
    }
}
