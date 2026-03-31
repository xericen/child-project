import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    showDropdown: boolean = false;
    showNotifications: boolean = false;
    showAllergyPanel: boolean = false;
    unreadCount: number = 0;
    notifications: any[] = [];
    role: string = '';

    allergyAlerts: any[] = [];
    allergyWeekStart: string = '';
    allergyWeekEnd: string = '';
    allergyCount: number = 0;

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();
        await this.loadRole();
        await this.loadUnreadCount();
        if (this.role === 'teacher' || this.role === 'director') {
            await this.loadAllergyAlerts();
        }
        await this.service.render();
    }

    private async loadRole() {
        try {
            const res = await wiz.call("get_role");
            if (res.code === 200) {
                this.role = res.data.role || '';
            }
        } catch (e) {
            this.role = '';
        }
    }

    private async loadUnreadCount() {
        try {
            const res = await wiz.call("get_unread_count");
            if (res.code === 200) {
                this.unreadCount = res.data.count || 0;
            }
        } catch (e) {
            this.unreadCount = 0;
        }
    }

    private async loadAllergyAlerts() {
        try {
            const res = await wiz.call("get_weekly_allergy");
            if (res.code === 200) {
                this.allergyAlerts = res.data.alerts || [];
                this.allergyWeekStart = res.data.week_start || '';
                this.allergyWeekEnd = res.data.week_end || '';
                this.allergyCount = this.allergyAlerts.length;
            }
        } catch (e) {
            this.allergyAlerts = [];
            this.allergyCount = 0;
        }
    }

    public async toggleAllergyPanel(event: Event) {
        event.stopPropagation();
        this.showAllergyPanel = !this.showAllergyPanel;
        this.showNotifications = false;
        this.showDropdown = false;
        await this.service.render();
    }

    public async toggleDropdown(event: Event) {
        event.stopPropagation();
        this.showDropdown = !this.showDropdown;
        this.showNotifications = false;
        this.showAllergyPanel = false;
        await this.service.render();
    }

    public async toggleNotifications(event: Event) {
        event.stopPropagation();
        this.showNotifications = !this.showNotifications;
        this.showDropdown = false;
        this.showAllergyPanel = false;
        if (this.showNotifications) {
            await this.loadNotifications();
        }
        await this.service.render();
    }

    private async loadNotifications() {
        try {
            const res = await wiz.call("get_notifications");
            if (res.code === 200) {
                this.notifications = res.data.notifications || [];
            }
        } catch (e) {
            this.notifications = [];
        }
    }

    public async readNotification(noti: any) {
        if (!noti.is_read) {
            await wiz.call("read_notification", { id: noti.id });
            noti.is_read = true;
            this.unreadCount = Math.max(0, this.unreadCount - 1);
        }
        this.showNotifications = false;
        if (noti.link) {
            this.router.navigateByUrl(noti.link);
        }
        await this.service.render();
    }

    public async readAll() {
        await wiz.call("read_all");
        this.unreadCount = 0;
        for (const n of this.notifications) {
            n.is_read = true;
        }
        await this.service.render();
    }

    public async closeAll() {
        this.showDropdown = false;
        this.showNotifications = false;
        this.showAllergyPanel = false;
        await this.service.render();
    }

    public async goMyInfo() {
        this.showDropdown = false;
        this.router.navigate(['/myinfo']);
    }

    public async goContact() {
        this.showDropdown = false;
        this.router.navigate(['/contact']);
    }

    public async leaveServer() {
        const res = await wiz.call("leave_server");
        if (res.code === 200) {
            this.showDropdown = false;
            this.router.navigate(['/']);
        }
    }

    public async logout() {
        const res = await wiz.call("logout");
        if (res.code === 200) {
            localStorage.removeItem('child_auto_login');
            this.showDropdown = false;
            this.router.navigate(['/main']);
        }
    }

    public timeAgo(dateStr: string): string {
        const now = new Date();
        const date = new Date(dateStr);
        const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
        if (diff < 60) return '방금 전';
        if (diff < 3600) return Math.floor(diff / 60) + '분 전';
        if (diff < 86400) return Math.floor(diff / 3600) + '시간 전';
        return Math.floor(diff / 86400) + '일 전';
    }
}
