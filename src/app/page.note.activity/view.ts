import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    foods: any[] = [];
    foodsLoading: boolean = true;
    selectedFood: any = null;
    activities: any[] = [];
    activityLoading: boolean = false;

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();
        await this.loadFoods();
        await this.service.render();
    }

    public formatMarkdown(text: string): string {
        if (!text) return '';
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
            .replace(/\*(.+?)\*/g, '<i>$1</i>')
            .replace(/\n/g, '<br>');
    }

    public goBack() {
        this.router.navigate(['/note']);
    }

    private async loadFoods() {
        this.foodsLoading = true;
        await this.service.render();
        const res = await wiz.call("get_weekly_foods");
        if (res.code === 200) {
            this.foods = res.data.foods || [];
        }
        this.foodsLoading = false;
        await this.service.render();
    }

    public async selectFood(food: any) {
        this.selectedFood = food;
        this.activities = [];
        this.activityLoading = true;
        await this.service.render();

        const res = await wiz.call("recommend_activity", { food: food.name });
        if (res.code === 200) {
            this.activities = res.data.activities || [];
        }
        this.activityLoading = false;
        await this.service.render();
    }

    public getTypeBadgeClass(type: string): string {
        if (type === '요리') return 'badge-cook';
        if (type === '체험') return 'badge-experience';
        if (type === '놀이') return 'badge-play';
        return '';
    }
}
