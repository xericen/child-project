import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    isEditing: boolean = false;

    email: string = '';
    role: string = '';
    nickname: string = '';
    phone: string = '';
    serverCode: string = '';

    childName: string = '';
    birthDate: string = '';
    twinType: string = '없음';

    allergies: any = { egg: false, milk: false, peanut: false };
    otherAllergy: string = '';
    isSevere: boolean = false;
    needsSubstitute: boolean = false;

    twinOptions: string[] = ['없음', '쌍둥이A', '쌍둥이B', '세쌍둥이A', '세쌍둥이B', '세쌍둥이C'];

    // 비밀번호 변경
    showPasswordChange: boolean = false;
    currentPassword: string = '';
    newPassword: string = '';
    confirmPassword: string = '';

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();
        await this.loadMyInfo();
        await this.service.render();
    }

    private async loadMyInfo() {
        const res = await wiz.call("get_myinfo");
        if (res.code === 200) {
            const d = res.data;
            this.email = d.email || '';
            this.role = d.role || '';
            this.nickname = d.nickname || '';
            this.phone = d.phone || '';
            this.serverCode = d.server_code || '';
            this.childName = d.child_name || '';
            this.birthDate = d.birth_date || '';
            this.twinType = d.twin_type || '없음';

            this.allergies = { egg: false, milk: false, peanut: false };
            this.otherAllergy = '';
            this.isSevere = false;
            this.needsSubstitute = false;

            if (d.allergies) {
                for (const a of d.allergies) {
                    if (a.allergy_type === '계란') this.allergies.egg = true;
                    else if (a.allergy_type === '우유') this.allergies.milk = true;
                    else if (a.allergy_type === '땅콩') this.allergies.peanut = true;
                    else if (a.allergy_type === '기타') this.otherAllergy = a.other_detail || '';
                    if (a.is_severe) this.isSevere = true;
                    if (a.needs_substitute) this.needsSubstitute = true;
                }
            }
        }
    }

    public formatPhone() {
        const digits = this.phone.replace(/\D/g, '').slice(0, 11);
        if (digits.length <= 3) {
            this.phone = digits;
        } else if (digits.length <= 7) {
            this.phone = digits.slice(0, 3) + '-' + digits.slice(3);
        } else {
            this.phone = digits.slice(0, 3) + '-' + digits.slice(3, 7) + '-' + digits.slice(7);
        }
    }

    public async startEdit() {
        this.isEditing = true;
        await this.service.render();
    }

    public async cancelEdit() {
        this.isEditing = false;
        await this.loadMyInfo();
        await this.service.render();
    }

    public async toggleAllergy(key: string) {
        this.allergies[key] = !this.allergies[key];
        await this.service.render();
    }

    public async toggleSevere() {
        this.isSevere = !this.isSevere;
        await this.service.render();
    }

    public async toggleSubstitute() {
        this.needsSubstitute = !this.needsSubstitute;
        await this.service.render();
    }

    public async selectTwin(option: string) {
        this.twinType = option;
        await this.service.render();
    }

    public async saveMyInfo() {
        const allergyList: any[] = [];
        if (this.allergies.egg) allergyList.push({ allergy_type: '계란' });
        if (this.allergies.milk) allergyList.push({ allergy_type: '우유' });
        if (this.allergies.peanut) allergyList.push({ allergy_type: '땅콩' });
        if (this.otherAllergy.trim()) {
            allergyList.push({ allergy_type: '기타', other_detail: this.otherAllergy.trim() });
        }

        const res = await wiz.call("save_myinfo", {
            nickname: this.nickname,
            phone: this.phone,
            birth_date: this.birthDate,
            twin_type: this.twinType,
            allergies: JSON.stringify(allergyList),
            is_severe: this.isSevere ? 'true' : 'false',
            needs_substitute: this.needsSubstitute ? 'true' : 'false'
        });

        if (res.code === 200) {
            alert('회원정보가 수정되었습니다.');
            this.isEditing = false;
            await this.loadMyInfo();
        } else {
            alert(res.data?.message || '저장에 실패했습니다.');
        }
        await this.service.render();
    }

    public async togglePasswordChange() {
        this.showPasswordChange = !this.showPasswordChange;
        this.currentPassword = '';
        this.newPassword = '';
        this.confirmPassword = '';
        await this.service.render();
    }

    public async changePassword() {
        if (!this.currentPassword) {
            alert('현재 비밀번호를 입력해주세요.');
            return;
        }
        if (this.newPassword.length < 4) {
            alert('새 비밀번호는 4자 이상이어야 합니다.');
            return;
        }
        if (this.newPassword !== this.confirmPassword) {
            alert('새 비밀번호가 일치하지 않습니다.');
            return;
        }

        const res = await wiz.call("change_password", {
            current_password: this.currentPassword,
            new_password: this.newPassword
        });

        if (res.code === 200) {
            alert('비밀번호가 변경되었습니다.');
            this.showPasswordChange = false;
            this.currentPassword = '';
            this.newPassword = '';
            this.confirmPassword = '';
        } else {
            alert(res.data?.message || '비밀번호 변경에 실패했습니다.');
        }
        await this.service.render();
    }

    public goBack() {
        this.router.navigate(['/note']);
    }
}
