import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    pendingUsers: any[] = [];

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();
        await this.loadPending();
        await this.service.render();
    }

    private async loadPending() {
        const res = await wiz.call("get_pending_users");
        if (res.code === 200) {
            this.pendingUsers = res.data.users || [];
        } else if (res.code === 403) {
            this.router.navigate(['/note']);
            return;
        }
    }

    public getRoleLabel(role: string): string {
        if (role === 'teacher') return '교사';
        if (role === 'parent') return '부모';
        return role;
    }

    public getDetail(user: any): string {
        if (user.role === 'teacher' && user.class_name) return user.class_name;
        if (user.role === 'parent' && user.child_name) return user.child_name;
        return '';
    }

    public async approveUser(user: any) {
        const res = await wiz.call("approve_user", { user_id: user.id });
        if (res.code === 200) {
            alert(`${user.nickname}님을 승인했습니다.`);
            this.pendingUsers = this.pendingUsers.filter((u: any) => u.id !== user.id);
        } else {
            alert(res.data?.message || '승인 처리에 실패했습니다.');
        }
        await this.service.render();
    }

    public async rejectUser(user: any) {
        if (!confirm(`${user.nickname}님의 가입을 거절하시겠습니까?`)) return;
        const res = await wiz.call("reject_user", { user_id: user.id });
        if (res.code === 200) {
            alert(`${user.nickname}님의 가입을 거절했습니다.`);
            this.pendingUsers = this.pendingUsers.filter((u: any) => u.id !== user.id);
        } else {
            alert(res.data?.message || '거절 처리에 실패했습니다.');
        }
        await this.service.render();
    }

    public goBack() {
        this.router.navigate(['/note']);
    }
}
