import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    public role: string = '';
    public selectedMonth: string = '';
    public loading: boolean = true;
    public selectedAge: string = '1~2세';
    public ageNutrition: any[] = [];
    public targetKcal: number = 420;
    public statsData: any = {};
    public statsCalendar: any[] = [];
    public calorieSufficient: number = 0;
    public calorieDeficient: number = 0;
    public deficientNutrients: any[] = [];
    public parentChildren: any[] = [];
    public allergyExpanded: boolean = false;
    public dailyCaloriesAll: any = {};

    constructor(public service: Service, public router: Router) { }

    public async ngOnInit() {
        await this.service.init();
        const now = new Date();
        this.selectedMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;

        const res = await wiz.call("get_role");
        if (res.code === 200) {
            this.role = res.data.role;
        }

        await this.loadAll();
        await this.service.render();
    }

    public get monthLabel(): string {
        const [y, m] = this.selectedMonth.split('-').map(Number);
        return `${y}년 ${m}월`;
    }

    private async loadAll() {
        this.loading = true;
        await this.service.render();
        try {
            await Promise.all([this.loadStats(), this.loadParentStats()]);
        } catch (e) {
            console.error('loadAll error:', e);
        }
        this.loading = false;
        await this.service.render();
    }

    private async loadStats() {
        const formData = new FormData();
        formData.append('month', this.selectedMonth);
        formData.append('age', this.selectedAge);
        const response = await fetch('/wiz/api/page.note.meal/get_stats', {
            method: 'POST',
            body: formData
        });
        const res = await response.json();
        if (res.code === 200) {
            this.statsData = res.data;
            const ageNut = res.data.age_nutrition || {};
            this.ageNutrition = Object.entries(ageNut).map(([label, val]: [string, any]) => ({
                label, kcal: val.kcal
            }));
            const sel = this.ageNutrition.find((a: any) => a.label === this.selectedAge);
            this.targetKcal = sel ? sel.kcal : (res.data.target_kcal || 420);
            this.dailyCaloriesAll = res.data.daily_calories_all || {};
            const dailyCal = res.data.daily_calories || {};
            this.buildCalorieCalendar(dailyCal);
        }
    }

    private async loadParentStats() {
        const formData = new FormData();
        const response = await fetch('/wiz/api/page.note.meal/get_parent_stats', {
            method: 'POST',
            body: formData
        });
        const res = await response.json();
        if (res.code === 200) {
            let children = res.data.children || [];
            if (this.role === 'director' || this.role === 'teacher') {
                children = children.filter((c: any) => c.allergy_types && c.allergy_types.length > 0);
            }
            this.parentChildren = children;
            if (this.parentChildren.length > 0) {
                const ageGroup = this.parentChildren[0].age_group;
                if (ageGroup && ageGroup !== this.selectedAge) {
                    this.selectedAge = ageGroup;
                    const sel = this.ageNutrition.find((a: any) => a.label === ageGroup);
                    if (sel) this.targetKcal = sel.kcal;
                    const ageCals = this.dailyCaloriesAll[ageGroup] || {};
                    this.buildCalorieCalendar(ageCals);
                }
            }
        }
    }

    private buildCalorieCalendar(dailyCal: any) {
        const [y, m] = this.selectedMonth.split('-').map(Number);
        const firstDay = new Date(y, m - 1, 1).getDay();
        const lastDate = new Date(y, m, 0).getDate();

        this.statsCalendar = [];
        for (let i = 0; i < firstDay; i++) {
            this.statsCalendar.push({ day: 0, kcal: 0, pct: 0, status: '' });
        }

        let sufficient = 0;
        let deficient = 0;
        for (let d = 1; d <= lastDate; d++) {
            const dateStr = `${this.selectedMonth}-${String(d).padStart(2, '0')}`;
            const kcal = dailyCal[dateStr] || 0;
            const pct = this.targetKcal > 0 ? Math.round(kcal / this.targetKcal * 100) : 0;
            let status = '';
            if (kcal > 0) {
                if (pct >= 90) { status = 'sufficient'; sufficient++; }
                else { status = 'deficient'; deficient++; }
            }
            this.statsCalendar.push({ day: d, kcal, pct, status });
        }
        this.calorieSufficient = sufficient;
        this.calorieDeficient = deficient;
    }

    public async selectAge(label: string) {
        this.selectedAge = label;
        const sel = this.ageNutrition.find((a: any) => a.label === label);
        if (sel) this.targetKcal = sel.kcal;
        const ageCals = this.dailyCaloriesAll[label] || {};
        this.buildCalorieCalendar(ageCals);
        await this.service.render();
    }

    public async prevMonth() {
        const [y, m] = this.selectedMonth.split('-').map(Number);
        const d = new Date(y, m - 2, 1);
        this.selectedMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        await this.loadAll();
    }

    public async nextMonth() {
        const [y, m] = this.selectedMonth.split('-').map(Number);
        const d = new Date(y, m, 1);
        this.selectedMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        await this.loadAll();
    }

    public goBack() {
        this.router.navigateByUrl('/note/meal');
    }
}
