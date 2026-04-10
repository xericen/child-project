import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    isEditing: boolean = false;
    activeTab: string = 'info';

    email: string = '';
    role: string = '';
    nickname: string = '';
    phone: string = '';
    serverCode: string = '';

    childName: string = '';
    birthDate: string = '';
    twinType: string = '없음';

    // 19종 표준 알레르기
    standardAllergies: any[] = [
        { num: 1, name: '난류(계란)', icon: '🥚', desc: '계란, 메추리알, 오리알 등', checked: false },
        { num: 2, name: '우유', icon: '🥛', desc: '우유, 치즈, 버터, 요거트 등', checked: false },
        { num: 3, name: '메밀', icon: '🌾', desc: '메밀국수, 메밀전병 등', checked: false },
        { num: 4, name: '땅콩', icon: '🥜', desc: '땅콩버터, 땅콩과자 등', checked: false },
        { num: 5, name: '대두', icon: '🫘', desc: '두부, 된장, 간장, 콩나물 등', checked: false },
        { num: 6, name: '밀', icon: '🌾', desc: '빵, 면, 과자, 부침개 등', checked: false },
        { num: 7, name: '고등어', icon: '🐟', desc: '고등어, 삼치 등 등푸른 생선', checked: false },
        { num: 8, name: '게', icon: '🦀', desc: '꽃게, 대게, 킹크랩 등', checked: false },
        { num: 9, name: '새우', icon: '🦐', desc: '새우, 젓갈 등', checked: false },
        { num: 10, name: '돼지고기', icon: '🥩', desc: '돼지고기, 햄, 소시지, 베이컨 등', checked: false },
        { num: 11, name: '복숭아', icon: '🍑', desc: '복숭아, 복숭아 주스 등', checked: false },
        { num: 12, name: '토마토', icon: '🍅', desc: '토마토, 토마토소스, 케첩 등', checked: false },
        { num: 13, name: '아황산류', icon: '⚗️', desc: '와인, 건조과일, 일부 음료 등', checked: false },
        { num: 14, name: '호두', icon: '🌰', desc: '호두, 호두과자 등', checked: false },
        { num: 15, name: '닭고기', icon: '🍗', desc: '닭고기, 치킨, 너겟 등', checked: false },
        { num: 16, name: '소고기', icon: '🥩', desc: '쇠고기, 불고기, 갈비 등', checked: false },
        { num: 17, name: '오징어', icon: '🦑', desc: '오징어, 오징어채 등', checked: false },
        { num: 18, name: '조개류', icon: '🐚', desc: '조개, 홍합, 굴, 전복 등', checked: false },
        { num: 19, name: '잣', icon: '🌲', desc: '잣, 잣죽 등', checked: false },
    ];
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

    public async switchTab(tab: string) {
        this.activeTab = tab;
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

            for (const a of this.standardAllergies) a.checked = false;
            this.otherAllergy = '';
            this.isSevere = false;
            this.needsSubstitute = false;

            if (d.allergies) {
                for (const a of d.allergies) {
                    if (a.allergy_type === '기타') {
                        this.otherAllergy = a.other_detail || '';
                    } else {
                        const atype = a.allergy_type;
                        const found = this.standardAllergies.find((s: any) =>
                            s.name === atype || s.name.split('(')[0] === atype ||
                            (s.name.includes('(') && s.name.split('(')[1]?.replace(')', '') === atype)
                        );
                        if (found) found.checked = true;
                    }
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

    public async toggleStandardAllergy(item: any) {
        item.checked = !item.checked;
        await this.service.render();
    }

    public get hasAnyAllergy(): boolean {
        return this.standardAllergies.some((a: any) => a.checked) || this.otherAllergy.trim().length > 0;
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
        for (const a of this.standardAllergies) {
            if (a.checked) {
                allergyList.push({ allergy_type: a.name });
            }
        }
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
