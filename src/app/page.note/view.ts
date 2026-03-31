import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    role: string = '';
    menuButtons: any[] = [];
    titleName: string = 'child';
    className: string = '';
    serverName: string = '';

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();
        await this.loadRole();
        await this.service.render();
    }

    private async loadRole() {
        const res = await wiz.call("get_role");
        if (res.code === 200) {
            this.role = res.data.role || 'parent';

            // 부모: childcheck 미완료 시 강제 이동
            if (this.role === 'parent' && res.data.childcheck_done === false) {
                this.router.navigate(['/childcheck']);
                return;
            }

            if (this.role === 'parent' && res.data.child_name) {
                this.titleName = res.data.child_name;
            } else if (this.role === 'director') {
                this.titleName = 'director';
            } else if (this.role === 'teacher') {
                this.titleName = 'teacher';
            }
            if (res.data.class_name) {
                this.className = res.data.class_name;
            }
            if (res.data.server_name) {
                this.serverName = res.data.server_name;
            }
        } else if (res.code === 401) {
            // 세션 만료 시 로그인 페이지로 리다이렉트
            localStorage.removeItem('child_auto_login');
            localStorage.removeItem('child_server_info');
            this.router.navigate(['/']);
            return;
        }
        this.buildMenu();
    }

    private buildMenu() {
        this.menuButtons = [
            { icon: '🍱', label: '오늘의 식단', path: '/note/today' },
            { icon: '📋', label: '식단표', path: '/note/meal' },
            { icon: '📷', label: '식단표 사진', path: '/note/photo' }
        ];

        if (this.role === 'parent') {
            this.menuButtons.push({ icon: '🎨', label: '활동 추천', path: '/note/activity' });
        }

        if (this.role === 'teacher') {
            this.menuButtons.push({ icon: '👶', label: '아이 프로필', path: '/note/profile' });
        }

        if (this.role === 'director') {
            this.menuButtons.push({ icon: '👤', label: '프로필', path: '/note/profile' });
            this.menuButtons.push({ icon: '✅', label: '가입 승인', path: '/note/approve' });
        }
    }

    public navigate(path: string) {
        this.router.navigate([path]);
    }
}
