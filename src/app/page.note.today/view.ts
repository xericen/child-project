import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    role: string = '';
    morningSnack: string = '';
    lunchMenu: string = '';
    afternoonSnack: string = '';
    allergyWarnings: any = {};

    // 저녁 추천 (부모용) - 3단계 분석
    dinnerLoading: boolean = false;
    showDinner: boolean = false;
    dinnerError: string = '';
    analysis: any = null;

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();
        await this.loadData();
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
        const keys = this.nutrientKeys();

        // 1. 원본 식단 텍스트에서 {{green:메뉴명}} 추출 (표시용)
        const greenNames = new Set<string>();
        const greenRegex = /\{\{green:(.*?)\}\}/g;
        for (const content of [this.morningSnack, this.lunchMenu, this.afternoonSnack]) {
            let m: any;
            while ((m = greenRegex.exec(content)) !== null) {
                const name = m[1].replace(/[ⓢⓄ①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳\d.]/g, '').trim();
                if (name) greenNames.add(name);
            }
        }

        // 2. Stage 1: 원본+대체식 모두 포함, 대체식은 합산에서 제외
        for (const meal of this.analysis.stage1.meals) {
            const items = meal.items || [];
            const sub: any = {};
            keys.forEach(k => {
                sub[k] = Math.round(items.filter((it: any) => !it.is_substitute && !greenNames.has(it.name))
                    .reduce((s: number, it: any) => s + (it[k] || 0), 0) * 10) / 10;
            });
            meal.subtotal = sub;
        }
        const rawTotal: any = {};
        keys.forEach(k => {
            rawTotal[k] = Math.round(
                this.analysis.stage1.meals.reduce((s: number, ml: any) => s + (ml.subtotal?.[k] || 0), 0) * 10
            ) / 10;
        });
        this.analysis.stage1.total = rawTotal;

        // 3. 끼니별(per-meal) 스케일링: DB kcal/protein이 있는 끼니만 비율 적용
        // 4. Stage 2: 스케일링 적용 + DAYCARE_TARGET 연령별 적용
        const DAYCARE_TARGETS: any = {
            '1~2': {calories: 420, protein: 9.3, fat: 14, carbs: 61, calcium: 210, iron: 2.8},
        };
        const childAge = this.analysis?.stage2?.age || 0;
        const DAYCARE_TARGET: any = DAYCARE_TARGETS['1~2'];
        if (this.analysis.stage2) {
            this.analysis.stage2.recommended = DAYCARE_TARGET;
        }

        if (this.analysis.stage2?.meals) {
            const consumed: any = {};
            keys.forEach(k => consumed[k] = 0);

            for (const meal of this.analysis.stage2.meals) {
                const s1 = this.analysis.stage1.meals.find((m: any) => m.meal_type === meal.meal_type);
                if (!s1) continue;

                // 끼니별 ratio 계산: DB kcal이 있으면 해당 끼니만 스케일링
                const mealApiCal = s1.subtotal?.calories || 0;
                const mealDbKcal = meal.target_kcal || 0;
                const mealDbProtein = meal.target_protein || 0;
                const mealApiProtein = s1.subtotal?.protein || 0;

                let kcalRatio = 1.0;
                if (mealDbKcal > 0 && mealApiCal > 0) {
                    kcalRatio = mealDbKcal / mealApiCal;
                }
                let pRatio = kcalRatio;
                if (mealDbProtein > 0 && mealApiProtein > 0) {
                    pRatio = mealDbProtein / mealApiProtein;
                }

                console.log(`[${meal.meal_type}] 스케일링: API=${mealApiCal}kcal → DB=${mealDbKcal}kcal, ratio=${kcalRatio.toFixed(4)}, protein: API=${mealApiProtein}g → DB=${mealDbProtein}g, ratio=${pRatio.toFixed(4)}`);

                meal.items = (s1.items || []).map((s1Item: any) => {
                    const scaled: any = { name: s1Item.name, source: s1Item.source };
                    keys.forEach(k => {
                        const r = (k === 'protein') ? pRatio : kcalRatio;
                        scaled[k] = Math.round((s1Item[k] || 0) * r * 10) / 10;
                    });
                    return scaled;
                });
                meal.scale_ratio = Math.round(kcalRatio * 10000) / 10000;

                const sub: any = {};
                keys.forEach(k => {
                    sub[k] = Math.round(meal.items.reduce((s: number, it: any) => s + (it[k] || 0), 0) * 10) / 10;
                    consumed[k] = Math.round((consumed[k] + sub[k]) * 10) / 10;
                });
                meal.subtotal = sub;
            }

            this.analysis.stage2.consumed = consumed;

            const rec = this.analysis.stage2.recommended || {};
            const deficit: any = {};
            const surplus: any = {};
            const status: any = {};
            keys.forEach(k => {
                const diff = Math.round(((consumed[k] || 0) - (rec[k] || 0)) * 10) / 10;
                if (diff < 0) {
                    deficit[k] = Math.round(Math.abs(diff) * 10) / 10;
                    surplus[k] = 0;
                    status[k] = '부족';
                } else if (diff > (rec[k] || 0) * 0.1) {
                    deficit[k] = 0;
                    surplus[k] = Math.round(diff * 10) / 10;
                    status[k] = '초과';
                } else {
                    deficit[k] = 0;
                    surplus[k] = 0;
                    status[k] = '적정';
                }
            });
            this.analysis.stage2.deficit = deficit;
            this.analysis.stage2.surplus = surplus;
            this.analysis.stage2.status = status;
        }
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
