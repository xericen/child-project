import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    role: string = '';
    morningSnack: string = '';
    lunchMenu: string = '';
    afternoonSnack: string = '';
    allergyWarnings: any = {};
    allergyDishes: any = {};
    mealKcal: any = {};
    dbKcal: number = 0;
    dbProtein: number = 0;
    pageLoading: boolean = true;
    currentPage: number = 0;
    mainIngredients: any[] = [];

    dinnerLoading: boolean = false;
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
            this.morningSnack = res.data.morning_snack || '';
            this.lunchMenu = res.data.lunch || '';
            this.afternoonSnack = res.data.afternoon_snack || '';
            this.allergyWarnings = res.data.allergy_warnings || {};
            this.allergyDishes = res.data.allergy_dishes || {};
            this.mealKcal = res.data.meal_kcal || {};
            this.dbKcal = res.data.db_kcal || 0;
            this.dbProtein = res.data.db_protein || 0;
        }
    }

    public async onDinnerClick() {
        if (this.analysis) {
            this.currentPage = 2;
            await this.service.render();
            return;
        }
        this.dinnerLoading = true;
        this.dinnerError = '';
        this.analysis = null;
        await this.service.render();

        try {
            const res = await wiz.call("recommend_dinner");
            if (res.code === 200 && res.data.analysis) {
                this.analysis = res.data.analysis;
                // DB 칼로리/단백질로 분석 결과 강제 동기화
                if (this.dbKcal > 0) {
                    if (this.analysis.stage1?.total) this.analysis.stage1.total.calories = this.dbKcal;
                    if (this.analysis.stage2?.consumed) this.analysis.stage2.consumed.calories = this.dbKcal;
                }
                if (this.dbProtein > 0) {
                    if (this.analysis.stage1?.total) this.analysis.stage1.total.protein = this.dbProtein;
                    if (this.analysis.stage2?.consumed) this.analysis.stage2.consumed.protein = this.dbProtein;
                }
                this.currentPage = 0;
                this.extractIngredients();
                this.logAnalysis();
            } else {
                this.dinnerError = res.data?.message || res.data?.error || '추천을 가져오지 못했습니다.';
            }
        } catch (e: any) {
            console.error('[recommendDinner] Error:', e);
            this.dinnerError = '서버 연결에 실패했습니다. 다시 시도해 주세요.';
        } finally {
            this.dinnerLoading = false;
            await this.service.render();
        }
    }

    private extractIngredients() {
        if (!this.analysis?.stage1?.meals) return;
        const names = new Set<string>();
        const childAllergies = new Set<string>();

        // 자녀 알레르기 키워드 수집
        for (const mt of Object.keys(this.allergyWarnings)) {
            for (const name of (this.allergyWarnings[mt] || [])) {
                childAllergies.add(name);
            }
        }

        for (const meal of this.analysis.stage1.meals) {
            for (const item of (meal.items || [])) {
                if (item.is_substitute) continue;
                const name = (item.name || '').replace(/[()（）]/g, ' ');
                // 주재료 추출: 2글자 이상 키워드
                const parts = name.split(/[\s,·+&/]+/).filter((p: string) => p.length >= 2);
                for (const p of parts) {
                    if (!['후식', '라이스', '그린', '미니'].includes(p)) {
                        names.add(p);
                    }
                }
            }
        }

        this.mainIngredients = Array.from(names).map(name => ({
            name,
            isAllergen: childAllergies.has(name) ||
                Array.from(childAllergies).some(a => name.includes(a) || a.includes(name))
        }));
    }

    private logAnalysis() {
        if (!this.analysis?.stage1?.meals) return;
        console.log('========== 저녁추천 영양 분석 결과 ==========');
        for (const meal of this.analysis.stage1.meals) {
            console.log(`\n[${meal.meal_type}]`);
            for (const item of (meal.items || [])) {
                const src = item.source || '?';
                console.log(`  ${item.name} (${src}) ${item.calories}kcal p=${item.protein}g f=${item.fat}g c=${item.carbs}g ca=${item.calcium}mg fe=${item.iron}mg`);
            }
        }
        console.log(`\n[총합] ${JSON.stringify(this.analysis.stage1.total)}`);
        console.log(`[목표] ${JSON.stringify(this.analysis.stage2?.recommended)}`);
        console.log(`[상태] ${JSON.stringify(this.analysis.stage2?.status)}`);
        console.log('==========================================');
    }

    public async goToPage(page: number) {
        this.currentPage = page;
        await this.service.render();
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

    public getNutrientStatus(key: string): string {
        return this.analysis?.stage2?.status?.[key] || '';
    }

    public getNutrientFillPercent(key: string): number {
        const rec = this.analysis?.stage2?.recommended?.[key] || 0;
        const consumed = this.analysis?.stage2?.consumed?.[key] || 0;
        if (rec <= 0) return 0;
        return Math.min(Math.round((consumed / rec) * 100), 100);
    }

    public nutrientKeys(): string[] {
        return ['calories', 'protein', 'fat', 'carbs', 'calcium', 'iron'];
    }

    public getDailyCaloriePercent(): number {
        const dailyTarget = this.analysis?.stage2?.daily_target?.calories || 0;
        const consumed = this.analysis?.stage2?.consumed?.calories || 0;
        if (dailyTarget <= 0) return 0;
        return Math.min(Math.round((consumed / dailyTarget) * 100), 100);
    }

    public getDailyCalorieDeficit(): number {
        return this.analysis?.stage2?.dinner_deficit?.calories || 0;
    }

    public getCalorieRingOffset(): number {
        const pct = this.getDailyCaloriePercent();
        const circumference = 2 * Math.PI * 48;
        return circumference - (circumference * pct / 100);
    }

    public getCalorieRingCircumference(): number {
        return 2 * Math.PI * 48;
    }

    public formatMealContent(content: string): string {
        if (!content) return '';
        const agePairs: [string, string][] = [['백김치', '배추김치']];
        for (const [young, old] of agePairs) {
            const pattern = new RegExp(young + '\\s*' + old, 'g');
            content = content.replace(pattern, young + '(1~2세)\n' + old + '(3~5세)');
        }
        return content.replace(/\{\{green:(.*?)\}\}/g, '<span class="green-text">$1</span>').replace(/\n/g, '<br>');
    }

    public hasAllergyWarning(mealType: string): boolean {
        return this.allergyWarnings[mealType] && this.allergyWarnings[mealType].length > 0;
    }

    public getAllergyText(mealType: string): string {
        if (!this.allergyWarnings[mealType]) return '';
        const dishes = this.allergyDishes[mealType] || [];
        if (dishes.length > 0) {
            return dishes.map((d: any) => `${d.dish}(${d.allergens.join(',')})`).join(', ');
        }
        return this.allergyWarnings[mealType].join(', ');
    }

    public goBack() {
        this.router.navigate(['/note']);
    }
}
