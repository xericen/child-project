import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    step: number = 1;

    childName: string = '';
    birthDate: string = '';
    age: number = 0;
    twinType: string = '없음';

    // 19종 표준 알레르기
    standardAllergies: any[] = [
        { num: 1, name: '난류(계란)', icon: '🥚', key: 'egg', desc: '계란, 메추리알, 오리알 등', checked: false },
        { num: 2, name: '우유', icon: '🥛', key: 'milk', desc: '우유, 치즈, 버터, 요거트 등', checked: false },
        { num: 3, name: '메밀', icon: '🌾', key: 'buckwheat', desc: '메밀국수, 메밀전병 등', checked: false },
        { num: 4, name: '땅콩', icon: '🥜', key: 'peanut', desc: '땅콩버터, 땅콩과자 등', checked: false },
        { num: 5, name: '대두', icon: '🫘', key: 'soybean', desc: '두부, 된장, 간장, 콩나물 등', checked: false },
        { num: 6, name: '밀', icon: '🌾', key: 'wheat', desc: '빵, 면, 과자, 부침개 등', checked: false },
        { num: 7, name: '고등어', icon: '🐟', key: 'mackerel', desc: '고등어, 삼치 등 등푸른 생선', checked: false },
        { num: 8, name: '게', icon: '🦀', key: 'crab', desc: '꽃게, 대게, 킹크랩 등', checked: false },
        { num: 9, name: '새우', icon: '🦐', key: 'shrimp', desc: '새우, 젓갈 등', checked: false },
        { num: 10, name: '돼지고기', icon: '🥩', key: 'pork', desc: '돼지고기, 햄, 소시지, 베이컨 등', checked: false },
        { num: 11, name: '복숭아', icon: '🍑', key: 'peach', desc: '복숭아, 복숭아 주스 등', checked: false },
        { num: 12, name: '토마토', icon: '🍅', key: 'tomato', desc: '토마토, 토마토소스, 케첩 등', checked: false },
        { num: 13, name: '아황산류', icon: '⚗️', key: 'sulfite', desc: '와인, 건조과일, 일부 음료 등', checked: false },
        { num: 14, name: '호두', icon: '🌰', key: 'walnut', desc: '호두, 호두과자 등', checked: false },
        { num: 15, name: '닭고기', icon: '🍗', key: 'chicken', desc: '닭고기, 치킨, 너겟 등', checked: false },
        { num: 16, name: '소고기', icon: '🥩', key: 'beef', desc: '쇠고기, 불고기, 갈비 등', checked: false },
        { num: 17, name: '오징어', icon: '🦑', key: 'squid', desc: '오징어, 오징어채 등', checked: false },
        { num: 18, name: '조개류', icon: '🐚', key: 'shellfish', desc: '조개, 홍합, 굴, 전복 등', checked: false },
        { num: 19, name: '잣', icon: '🌲', key: 'pinenut', desc: '잣, 잣죽 등', checked: false },
    ];
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

            // 19종 알레르기 복원
            for (const a of this.standardAllergies) a.checked = false;
            this.otherAllergy = '';
            const allergyList: any[] = res.data.allergies || [];
            for (const a of allergyList) {
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

    public async goStep3() {
        this.step = 3;
        await this.service.render();
    }

    public async prevStep() {
        if (this.step > 1) {
            this.step--;
            await this.service.render();
        }
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

    public async saveChildcheck() {
        const allergyList: any[] = [];
        for (const a of this.standardAllergies) {
            if (a.checked) {
                const typeName = a.name.includes('(') ? a.name.split('(')[0] : a.name;
                allergyList.push({ allergy_type: typeName });
            }
        }
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
