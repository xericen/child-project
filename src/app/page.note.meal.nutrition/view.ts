import { OnInit } from '@angular/core';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    public role: string = '';
    public selectedMonth: string = '';
    public selectedAge: string = '1~2세';
    public ages: string[] = ['1~2세'];
    public loading: boolean = true;

    // Dashboard data
    public totalDays: number = 0;
    public dailyCalories: any = {};
    public nutrients: any = {};
    public nutrientList: any[] = [];
    public deficientNutrients: any[] = [];
    public summary: string = '';
    public cachedAt: string = '';

    // Calendar
    public calendarDays: any[] = [];
    public sufficientDays: number = 0;
    public deficientDays: number = 0;

    constructor(public service: Service) { }

    public async ngOnInit() {
        await this.service.init();
        const now = new Date();
        this.selectedMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;

        const res = await wiz.call("get_role");
        if (res.code === 200) {
            this.role = res.data.role;
        }

        await this.loadDashboard();
        await this.service.render();
    }

    private async loadDashboard(refresh: boolean = false) {
        this.loading = true;
        await this.service.render();

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 120000);
            const formData = new FormData();
            formData.append('month', this.selectedMonth);
            formData.append('age', this.selectedAge);
            if (refresh) formData.append('refresh', 'true');

            const response = await fetch('/wiz/api/page.note.meal.nutrition/get_dashboard', {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            const res = await response.json();

            if (res.code === 200) {
                this.totalDays = res.data.total_days || 0;
                this.dailyCalories = res.data.daily_calories || {};
                this.nutrients = res.data.nutrients || {};
                this.deficientNutrients = res.data.deficient_nutrients || [];
                this.summary = res.data.summary || '';
                this.cachedAt = res.data.cached_at || '';
                if (res.data.ages) this.ages = res.data.ages;
                this.buildNutrientList();
                this.buildCalendar();
            }
        } catch (e: any) {
            console.error('loadDashboard error:', e);
        }

        this.loading = false;
        await this.service.render();
    }

    private buildNutrientList() {
        this.nutrientList = Object.entries(this.nutrients).map(([name, val]: [string, any]) => ({
            name,
            key: val.key || '',
            percent: Math.min(val.percent || 0, 100),
            target: val.target || '',
            targetValue: val.target_value || 0,
            avgDaily: val.avg_daily || 0,
            status: val.status || '',
            unit: val.unit || '',
            sufficient: (val.percent || 0) >= 80
        }));
    }

    private buildCalendar() {
        const [y, m] = this.selectedMonth.split('-').map(Number);
        const firstDay = new Date(y, m - 1, 1).getDay();
        const lastDate = new Date(y, m, 0).getDate();
        const targetKcal = this.getTargetKcal();

        this.calendarDays = [];
        for (let i = 0; i < firstDay; i++) {
            this.calendarDays.push({ day: 0, kcal: 0, pct: 0, status: '' });
        }

        let sufficient = 0;
        let deficient = 0;
        for (let d = 1; d <= lastDate; d++) {
            const dateStr = `${this.selectedMonth}-${String(d).padStart(2, '0')}`;
            const kcal = this.dailyCalories[dateStr] || 0;
            const pct = targetKcal > 0 ? Math.round(kcal / targetKcal * 100) : 0;
            let status = '';
            if (kcal > 0) {
                if (pct >= 90) { status = 'sufficient'; sufficient++; }
                else { status = 'deficient'; deficient++; }
            }
            this.calendarDays.push({ day: d, kcal, pct, status, date: dateStr });
        }
        this.sufficientDays = sufficient;
        this.deficientDays = deficient;
    }

    private getTargetKcal(): number {
        const cal = this.nutrients['열량'];
        return cal ? (cal.targetValue || 420) : 420;
    }

    public getMaxDailyCalorie(): number {
        const vals = Object.values(this.dailyCalories) as number[];
        return vals.length > 0 ? Math.max(...vals) : 1;
    }

    public getDailyCalorieEntries(): any[] {
        const [y, m] = this.selectedMonth.split('-').map(Number);
        const lastDate = new Date(y, m, 0).getDate();
        const entries: any[] = [];
        for (let d = 1; d <= lastDate; d++) {
            const dateStr = `${this.selectedMonth}-${String(d).padStart(2, '0')}`;
            const kcal = this.dailyCalories[dateStr] || 0;
            const dayOfWeek = new Date(y, m - 1, d).getDay();
            if (dayOfWeek === 0 || dayOfWeek === 6) continue;
            entries.push({ day: d, kcal, dateStr });
        }
        return entries;
    }

    public getBarHeight(kcal: number): number {
        const max = this.getMaxDailyCalorie();
        return max > 0 ? Math.round((kcal / max) * 100) : 0;
    }

    public getBarColor(kcal: number): string {
        const target = this.getTargetKcal();
        const pct = target > 0 ? (kcal / target * 100) : 0;
        if (pct >= 90) return '#22c55e';
        if (pct >= 70) return '#f59e0b';
        return '#ef4444';
    }

    public getNutrientColor(percent: number): string {
        if (percent >= 80) return '#22c55e';
        if (percent >= 60) return '#f59e0b';
        return '#ef4444';
    }

    public async selectAge(age: string) {
        this.selectedAge = age;
        await this.loadDashboard();
    }

    public async prevMonth() {
        const [y, m] = this.selectedMonth.split('-').map(Number);
        const d = new Date(y, m - 2, 1);
        this.selectedMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        await this.loadDashboard();
    }

    public async nextMonth() {
        const [y, m] = this.selectedMonth.split('-').map(Number);
        const d = new Date(y, m, 1);
        this.selectedMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        await this.loadDashboard();
    }

    public async refresh() {
        await this.loadDashboard(true);
    }

    public goBack() {
        this.service.href('/note/meal');
    }
}
