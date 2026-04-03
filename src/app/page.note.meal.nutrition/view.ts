import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    public role: string = '';
    public selectedMonth: string = '';
    public loading: boolean = true;

    // Dashboard data
    public totalDays: number = 0;
    public nutrients: any = {};
    public nutrientList: any[] = [];
    public deficientNutrients: any[] = [];
    public summary: string = '';
    public cachedAt: string = '';

    constructor(public service: Service, public router: Router) { }

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
                this.nutrients = res.data.nutrients || {};
                this.deficientNutrients = res.data.deficient_nutrients || [];
                this.summary = res.data.summary || '';
                this.cachedAt = res.data.cached_at || '';
                this.buildNutrientList();
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

    public getNutrientColor(percent: number): string {
        if (percent >= 80) return '#22c55e';
        if (percent >= 60) return '#f59e0b';
        return '#ef4444';
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
        this.router.navigateByUrl('/note/meal');
    }
}
