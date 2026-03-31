import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    step: number = 1;

    childName: string = '';
    birthDate: string = '';
    age: number = 0;
    twinType: string = '없음';

    allergies: any = {
        egg: false,
        milk: false,
        peanut: false
    };
    otherAllergy: string = '';
    isSevere: boolean = false;
    needsSubstitute: boolean = false;

    twinOptions: string[] = ['없음', '쌍둥이A', '쌍둥이B', '세쌍둥이A', '세쌍둥이B', '세쌍둥이C'];

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();
        await this.loadChildInfo();
        await this.service.render();
    }

    private async loadChildInfo() {
        const res = await wiz.call("get_child_info");
        if (res.code === 200) {
            this.childName = res.data.child_name || '';
            this.birthDate = res.data.birth_date || '';
            if (this.birthDate) {
                this.age = this.calcAge(this.birthDate);
            }
            this.twinType = res.data.twin_type || '없음';
            this.isSevere = res.data.is_severe === true;
            this.needsSubstitute = res.data.needs_substitute === true;

            // 기존 알레르기 체크박스 복원
            this.allergies = { egg: false, milk: false, peanut: false };
            this.otherAllergy = '';
            const allergyList: any[] = res.data.allergies || [];
            for (const a of allergyList) {
                if (a.allergy_type === '계란') this.allergies.egg = true;
                else if (a.allergy_type === '우유') this.allergies.milk = true;
                else if (a.allergy_type === '땅콩') this.allergies.peanut = true;
                else if (a.allergy_type === '기타') this.otherAllergy = a.other_detail || '';
            }
        }
    }

    private calcAge(birthDate: string): number {
        const today = new Date();
        const birth = new Date(birthDate);
        let age = today.getFullYear() - birth.getFullYear();
        const m = today.getMonth() - birth.getMonth();
        if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) {
            age--;
        }
        return age;
    }

    public async goStep2() {
        this.step = 2;
        await this.service.render();
    }

    public async prevStep() {
        if (this.step > 1) {
            this.step--;
            await this.service.render();
        }
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

    public async saveChildcheck() {
        const allergyList: any[] = [];
        if (this.allergies.egg) allergyList.push({ allergy_type: '계란' });
        if (this.allergies.milk) allergyList.push({ allergy_type: '우유' });
        if (this.allergies.peanut) allergyList.push({ allergy_type: '땅콩' });
        if (this.otherAllergy.trim()) {
            allergyList.push({ allergy_type: '기타', other_detail: this.otherAllergy.trim() });
        }

        const res = await wiz.call("save_childcheck", {
            child_name: this.childName,
            birth_date: this.birthDate,
            twin_type: this.twinType,
            allergies: JSON.stringify(allergyList),
            is_severe: this.isSevere ? 'true' : 'false',
            needs_substitute: this.needsSubstitute ? 'true' : 'false'
        });

        if (res.code === 200) {
            localStorage.setItem('hasCompletedAllergyCheck', 'true');
            alert('아이 정보가 저장되었습니다!');
            this.router.navigate(['/note']);
        } else {
            alert(res.data?.message || '저장에 실패했습니다.');
        }
        await this.service.render();
    }
}
