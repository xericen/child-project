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
            this.allergyDishes = res.data.allergy_dishes || {};
        }
    }

    public async recommendDinner() {
        this.dinnerLoading = true;
        this.showDinner = true;
        this.dinnerError = '';
        this.analysis = null;
        await this.service.render();

        try {
            const res = await wiz.call("recommend_dinner");
            if (res.code === 200 && res.data.analysis) {
                this.analysis = res.data.analysis;
                this.fixGreenAndScaling();
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

    private fixGreenAndScaling() {
        if (!this.analysis?.stage1?.meals) return;
        console.log('========== 저녁추천 영양 분석 결과 ==========');
        for (const meal of this.analysis.stage1.meals) {
            console.log(`\n[${meal.meal_type}]`);
            for (const item of (meal.items || [])) {
                const sub = item.is_substitute ? ' (대체식)' : '';
                const est = item.is_estimated ? ' (AI추정)' : '';
                const matched = item.matched_name ? ` → 매칭: "${item.matched_name}"` : ' → 매칭실패';
                const src = item.source || '?';
                const serving = item.serving_size || '?';
                const ratio = item.serving_ratio && item.serving_ratio !== 1 ? ` ×${item.serving_ratio}` : '';
                const cat = item.category ? ` [${item.category}]` : '';
                console.log(`  📌 ${item.name}${sub}${est}${matched} | 소스: ${src} | ${serving}${ratio}${cat}`);
                console.log(`     칼로리: ${item.calories || 0}kcal | 단백질: ${item.protein || 0}g | 지방: ${item.fat || 0}g | 탄수화물: ${item.carbs || 0}g | 칼슘: ${item.calcium || 0}mg | 철분: ${item.iron || 0}mg`);
            }
            if (meal.subtotal) {
                console.log(`  [소계] ${meal.subtotal.calories || 0}kcal`);
            }
        }
        console.log(`\n[총합] 칼로리: ${this.analysis.stage1.total?.calories || 0}kcal, 단백질: ${this.analysis.stage1.total?.protein || 0}g`);
        console.log('\n[Stage2 - 목표 대비]');
        console.log('  섭취량:', this.analysis.stage2?.consumed);
        console.log('  권장량:', this.analysis.stage2?.recommended);
        console.log('  부족분:', this.analysis.stage2?.deficit);
        console.log('  상태:', this.analysis.stage2?.status);
        if (this.analysis.stage3?.error) {
            console.error('\n[Stage3 에러]', this.analysis.stage3.error);
            if (this.analysis.stage3.traceback) {
                console.error('[traceback]', this.analysis.stage3.traceback);
            }
        }
        if (this.analysis.stage3?.menus?.length) {
            console.log(`\n[Stage3 추천] ${this.analysis.stage3.menus.length}개 메뉴`);
            for (const m of this.analysis.stage3.menus) {
                console.log(`  🍳 ${m.name}: ${m.nutrients?.calories || 0}kcal — ${m.reason || ''}`);
            }
        }
        console.log('==========================================');
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
        // 연령별 연결 메뉴 분리 표시 (백김치배추김치 → 백김치(1~2세) / 배추김치(3~5세))
        const agePairs: [string, string][] = [['백김치', '배추김치']];
        for (const [young, old] of agePairs) {
            const pattern = new RegExp(young + '\\s*' + old, 'g');
            content = content.replace(pattern, young + '(1~2\uc138)\n' + old + '(3~5\uc138)');
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
