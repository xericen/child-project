import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    role: string = '';
    morningSnack: string = '';
    lunchMenu: string = '';
    afternoonSnack: string = '';
    allergyWarnings: any = {};
    pageLoading: boolean = true;

    // 저녁 추천 (부모용) - 3단계 분석
    dinnerLoading: boolean = false;
    showDinner: boolean = false;
    dinnerError: string = '';
    analysis: any = null;

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();
        await this.service.render();
        await this.loadData();
        this.pageLoading = false;
        await this.service.render();
    }

    private async loadData() {
        const res = await wiz.call("get_today_menu");
        if (res.code === 200) {
            this.role = res.data.role || 'parent';
            this.morningSnack = res.data.morning_snack || '등록된 오전간식이 없습니다.';
            this.lunchMenu = res.data.lunch || '등록된 점심 식단이 없습니다.';
            this.afternoonSnack = res.data.afternoon_snack || '등록된 오후간식이 없습니다.';
            this.allergyWarnings = res.data.allergy_warnings || {};
        }
    }

    public async recommendDinner() {
        this.dinnerLoading = true;
        this.showDinner = true;
        this.dinnerError = '';
        this.analysis = null;
        await this.service.render();

        const res = await wiz.call("recommend_dinner");
        this.dinnerLoading = false;
        if (res.code === 200 && res.data.analysis) {
            this.analysis = res.data.analysis;
            this.fixGreenAndScaling();
            console.log('Stage 1 - green 제외 + 스케일링 보정 후', this.analysis.stage1);
            console.log('Stage 2 - 권장량 대비', this.analysis.stage2);
            console.log('Stage 3 - AI 저녁 추천', this.analysis.stage3);
        } else {
            this.dinnerError = res.data?.error || '추천을 가져오지 못했습니다.';
        }
        await this.service.render();
    }

    private fixGreenAndScaling() {
        if (!this.analysis?.stage1?.meals) return;
        // 서버가 이미 DB kcal/protein 기준으로 원본 아이템만 스케일링 완료
        // 프론트엔드는 서버 값을 그대로 사용, 재계산 금지
        console.log('[Stage1] 서버 반환값:', this.analysis.stage1.total);
        console.log('[Stage2] consumed:', this.analysis.stage2?.consumed);
        console.log('[Stage2] recommended:', this.analysis.stage2?.recommended);
        console.log('[Stage2] status:', this.analysis.stage2?.status);
    }

    public getNutrientLabel(key: string): string {
        const labels: any = {
            calories: '칼로리', protein: '단백질', fat: '지방',
            carbs: '탄수화물', calcium: '칼슘', iron: '철분'
        };
        return labels[key] || key;
    }

    public getNutrientUnit(key: string): string {
        const units: any = {
            calories: 'kcal', protein: 'g', fat: 'g',
            carbs: 'g', calcium: 'mg', iron: 'mg'
        };
        return units[key] || '';
    }

    public getDeficitPercent(deficit: any, recommended: any, key: string): number {
        if (!recommended || !recommended[key] || recommended[key] === 0) return 0;
        const consumed = (recommended[key] - (deficit[key] || 0));
        return Math.round((consumed / recommended[key]) * 100);
    }

    public getNutrientStatus(key: string): string {
        return this.analysis?.stage2?.status?.[key] || '';
    }

    public nutrientKeys(): string[] {
        return ['calories', 'protein', 'fat', 'carbs', 'calcium', 'iron'];
    }

    public formatMealContent(content: string): string {
        if (!content) return '';
        return content.replace(/\{\{green:(.*?)\}\}/g, '<span class="green-text">$1</span>');
    }

    public hasAllergyWarning(mealType: string): boolean {
        return this.allergyWarnings[mealType] && this.allergyWarnings[mealType].length > 0;
    }

    public getAllergyText(mealType: string): string {
        if (!this.allergyWarnings[mealType]) return '';
        return this.allergyWarnings[mealType].join(', ');
    }

    public goBack() {
        this.router.navigate(['/note']);
    }
}
