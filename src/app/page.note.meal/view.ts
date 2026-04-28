import { OnInit, ViewChild, ElementRef } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    @ViewChild('fileInput') fileInput: ElementRef;
    @ViewChild('hwpFileInput') hwpFileInput: ElementRef;

    role: string = '';
    mode: string = 'calendar';
    calendarTab: string = 'calendar';
    selectedDate: string = new Date().toISOString().substring(0, 10);
    selectedMonth: string = new Date().toISOString().substring(0, 7);
    meals: any[] = [];
    monthlyMeals: any = {};
    calendarDays: any[] = [];

    newMealType: string = '점심';
    newMealContent: string = '';
    selectedFile: File | null = null;
    showForm: boolean = false;

    // 테마 정보
    readonly MEAL_THEMES: any = {
        '이달의식재료': { emoji: '🥬', color: '#2E7D32' },
        '세계밥상': { emoji: '🌍', color: '#1565C0' },
        '상영양식': { emoji: '🥗', color: '#F9A825' },
        '차차밥상': { emoji: '🍵', color: '#8B4513' },
        '新메뉴': { emoji: '⭐', color: '#7B1FA2' },
        '신선식품': { emoji: '🍎', color: '#E65100' },
        '대체식': { emoji: '🔄', color: '#C62828' },
    };

    mealFiles: any[] = [];
    monthFiles: any[] = [];
    currentMonthLabel: string = '';
    nextMonthLabel: string = '';
    selectedMealFile: File | null = null;
    uploadTargetMonth: string = '';
    allUploadMonths: string[] = [];

    // 식단 수정
    editingMealId: number | null = null;
    editMealType: string = '';
    editMealContent: string = '';

    // HWP 파싱 로딩
    hwpLoading: boolean = false;
    hwpProgress: number = 0;
    hwpProgressLabel: string = '';
    private _hwpProgressTimer: any = null;
    private _hwpTarget: number = 0;
    private _hwpStartTime: number = 0;

    // 월간 HWP 파일 상태
    monthHwpFile: any = null;

    // 통계
    statsData: any = {};
    statsLoading: boolean = false;
    aiLoading: boolean = false;
    reparseLoading: boolean = false;
    aiData: any = {};
    statsCalendar: any[] = [];
    calorieSufficient: number = 0;
    calorieDeficient: number = 0;
    nutrientList: any[] = [];
    deficientNutrients: any[] = [];
    aiSummary: string = '';
    aiCachedAt: string = '';
    aiDataChanged: boolean = false;
    aiError: string = '';
    targetKcal: number = 420;
    ageNutrition: any[] = [];
    selectedAge: string = '1~2세';
    dailyCaloriesAll: any = {};  // 연령별 전체: {'1~2세': {date: kcal}, '3~5세': {date: kcal}}

    // 부모용 맞춤 통계
    parentData: any = {};
    parentChildren: any[] = [];
    allergyExpanded: boolean = false;

    // 대체식 토글 로딩
    substituteLoading: boolean = false;

    // 영양분석 대시보드 (nutrition page 통합)
    nutritionData: any = {};
    nutritionLoading: boolean = false;
    nutritionNutrientList: any[] = [];
    nutritionDeficients: any[] = [];
    nutritionSummary: string = '';
    nutritionCachedAt: string = '';
    nutritionEstimatedCount: number = 0;
    nutritionTotalMenuCount: number = 0;

    // 날짜 이동 요청 취소용
    private _dailyRequestId: number = 0;
    dailyLoading: boolean = false;
    dailyCache: any = {};
    private dailyFetchPromises: any = {};

    // 영양 정보 (연령별)
    nutritionByAge: any = {};
    nutritionAgeKeys: string[] = [];
    selectedNutritionAge: string = '';
    nutritionAllergens: string[] = [];

    public get nutrition(): any {
        return this.nutritionByAge[this.selectedNutritionAge] || null;
    }

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();
        const res = await wiz.call("get_role");
        if (res.code === 200) {
            this.role = res.data.role || 'parent';
        }
        const now = new Date();
        this.selectedDate = this.formatDate(now);
        this.selectedMonth = this.selectedDate.substring(0, 7);
        await this.loadMealFiles();
        await this.loadMonthly();
        await this.prefetchCurrentMonthDailyData(false, undefined, false);
        await this.service.render();
        const [y, m] = this.selectedMonth.split('-').map(Number);
        return `${y}년 ${m}월`;
    }

    public get monthLabel(): string {
        const [y, m] = this.selectedMonth.split('-').map(Number);
        return `${y}년 ${m}월`;
    }

    public get totalFileCount(): number {
        const currentFiles = this.monthFiles.find((g: any) => g.month === this.selectedMonth);
        return currentFiles ? (currentFiles.files || []).length : 0;
    }

    public get todayStr(): string {
        return this.formatDate(new Date());
    }

    public get currentMonthFiles(): any[] {
        const group = this.monthFiles.find((g: any) => g.month === this.selectedMonth);
        return group ? (group.files || []) : [];
    }

    public get groupedMonthFiles(): any[] {
        const files = this.currentMonthFiles;
        const groups: any = {};
        for (const file of files) {
            const dateStr = (file.created_at || '').substring(0, 10);
            if (!groups[dateStr]) groups[dateStr] = [];
            groups[dateStr].push(file);
        }
        return Object.keys(groups).sort().reverse().map(date => {
            const [, m, d] = date.split('-').map(Number);
            return {
                date,
                label: `${m}월 ${d}일`,
                files: groups[date]
            };
        });
    }

    public fileTime(file: any): string {
        const ca = file.created_at || '';
        return ca.length >= 16 ? ca.substring(11, 16) : ca;
    }

    public async switchTab(tab: string) {
        this.calendarTab = tab;
        await this.service.render();
    }

    private formatDate(d: Date): string {
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const dd = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${dd}`;
    }

    public async goBack() {
        if (this.mode !== 'calendar') {
            this.mode = 'calendar';
            this.showForm = false;
            this.editingMealId = null;
            await this.loadMonthly();
            await this.prefetchCurrentMonthDailyData(false, undefined, true);
            await this.service.render();
        }
        this.router.navigate(['/note']);
    }

    public async goNutrition() {
        this.mode = 'nutrition';
        this.statsLoading = true;
        this.parentChildren = [];
        this.deficientNutrients = [];
        await this.service.render();
        try {
            await Promise.all([this.loadStats(), this.loadParentStats()]);
        } catch (e) {
            console.error('goNutrition error:', e);
        } finally {
            this.statsLoading = false;
            await this.service.render();
        }
    }

    private async loadNutritionDashboard(refresh: boolean = false) {
        try {
            const formData = new FormData();
            formData.append('month', this.selectedMonth);
            if (refresh) formData.append('refresh', 'true');
            const response = await fetch('/wiz/api/page.note.meal.nutrition/get_dashboard', {
                method: 'POST',
                body: formData
            });
            const res = await response.json();
            if (res.code === 200) {
                this.nutritionData = res.data;
                this.nutritionSummary = res.data.summary || '';
                this.nutritionCachedAt = res.data.cached_at || '';
                this.nutritionEstimatedCount = res.data.estimated_count || 0;
                this.nutritionTotalMenuCount = res.data.total_menu_count || 0;
                this.nutritionDeficients = res.data.deficient_nutrients || [];
                const nutrients = res.data.nutrients || {};
                this.nutritionNutrientList = Object.entries(nutrients).map(([name, val]: [string, any]) => ({
                    name,
                    percent: Math.min(val.percent || 0, 100),
                    target: val.target || '',
                    avgDaily: val.avg_daily || 0,
                    unit: val.unit || '',
                    sufficient: (val.percent || 0) >= 80
                }));
            }
        } catch (e) {
            console.error('loadNutritionDashboard error:', e);
        }
    }

    public getNutrientColor(percent: number): string {
        if (percent >= 80) return '#22c55e';
        if (percent >= 60) return '#f59e0b';
        return '#ef4444';
    }

    private async loadMonthly() {
        const res = await wiz.call("get_monthly", { month: this.selectedMonth });
        if (res.code === 200) {
            this.monthlyMeals = res.data.meals || {};
            this.buildCalendar();
        }
        await this.loadMonthHwp();
    }

    private async loadMonthHwp() {
        const res = await wiz.call("get_month_hwp", { month: this.selectedMonth });
        if (res.code === 200) {
            this.monthHwpFile = res.data.hwp_file || null;
        }
    }

    private buildCalendar() {
        const [y, m] = this.selectedMonth.split('-').map(Number);
        const firstDay = new Date(y, m - 1, 1).getDay();
        const lastDate = new Date(y, m, 0).getDate();
        this.calendarDays = [];
        for (let i = 0; i < firstDay; i++) {
            this.calendarDays.push({ day: '', hasMeal: false, dow: i });
        }
        for (let d = 1; d <= lastDate; d++) {
            const dateStr = `${this.selectedMonth}-${String(d).padStart(2, '0')}`;
            const dayMeals = this.monthlyMeals[dateStr] || [];
            const theme = dayMeals.length > 0 ? (dayMeals[0].theme || '') : '';
            const dow = (firstDay + d - 1) % 7;
            this.calendarDays.push({
                day: d,
                date: dateStr,
                hasMeal: dayMeals.length > 0,
                theme: theme,
                dow: dow
            });
        }
    }

    private getAvailableMealDates(): string[] {
        return Object.keys(this.monthlyMeals || {})
            .filter((date) => Array.isArray(this.monthlyMeals[date]) && this.monthlyMeals[date].length > 0)
            .sort();
    }

    private getFirstMealDateInSelectedMonth(): string {
        const dates = this.getAvailableMealDates();
        return dates.length > 0 ? dates[0] : `${this.selectedMonth}-01`;
    }

    private getAdjacentMealDate(direction: 'prev' | 'next'): string | null {
        const dates = this.getAvailableMealDates();
        if (dates.length === 0) return null;
        if (!this.selectedDate || !dates.includes(this.selectedDate)) {
            return direction === 'prev' ? dates[dates.length - 1] : dates[0];
        }
        const currentIndex = dates.indexOf(this.selectedDate);
        if (direction === 'prev') {
            return currentIndex > 0 ? dates[currentIndex - 1] : null;
        }
        return currentIndex < dates.length - 1 ? dates[currentIndex + 1] : null;
    }

    private resetDailyState() {
        this.meals = [];
        this.nutritionByAge = {};
        this.nutritionAgeKeys = [];
        this.selectedNutritionAge = '';
        this.nutritionAllergens = [];
    }

    private applyDailyData(data: any) {
        this.meals = data?.meals || [];
        this.nutritionByAge = data?.nutrition_by_age || {};
        this.nutritionAgeKeys = Object.keys(this.nutritionByAge);
        if (!this.nutritionAgeKeys.includes(this.selectedNutritionAge)) {
            this.selectedNutritionAge = this.nutritionAgeKeys[0] || '';
        }
        this.nutritionAllergens = data?.allergens || [];
    }

    private seedDailyFromMonthly(date: string) {
        const sourceMeals = Array.isArray(this.monthlyMeals?.[date]) ? this.monthlyMeals[date] : [];
        if (sourceMeals.length === 0) {
            this.resetDailyState();
            return;
        }
        this.meals = sourceMeals.map((meal: any) => ({
            id: meal.id,
            meal_type: meal.meal_type,
            content: meal.content || '',
            photo_path: meal.photo_path || '',
            theme: meal.theme || '',
            allergy_match: false,
            matched_allergens: [],
            matched_dishes: [],
            substitute_pairs: []
        }));
        this.nutritionByAge = {};
        this.nutritionAgeKeys = [];
        this.selectedNutritionAge = '';
        this.nutritionAllergens = [];
    }

    private async fetchDailyData(date: string, force: boolean = false, skipNutrition: boolean = false): Promise<any> {
        if (!force && this.dailyCache[date]) {
            return this.dailyCache[date];
        }
        if (!force && this.dailyFetchPromises[date]) {
            return await this.dailyFetchPromises[date];
        }

        const params: any = { date };
        if (skipNutrition) params.skip_nutrition = "1";

        this.dailyFetchPromises[date] = (async () => {
            const res = await wiz.call("get_daily", params);
            if (res.code === 200) {
                this.dailyCache[date] = res.data || {};
                return this.dailyCache[date];
            }
            return null;
        })();

        try {
            return await this.dailyFetchPromises[date];
        } finally {
            delete this.dailyFetchPromises[date];
        }
    }

    private async prefetchDailyDates(dates: string[], concurrency: number = 4, onProgress?: (done: number, total: number) => void, skipNutrition: boolean = false) {
        const queue = dates.filter((date) => !!date && !this.dailyCache[date]);
        if (queue.length === 0) {
            if (onProgress) onProgress(1, 1);
            return;
        }

        let index = 0;
        let completed = 0;
        const total = queue.length;
        const workers = Array.from({ length: Math.min(concurrency, queue.length) }, async () => {
            while (index < queue.length) {
                const currentIndex = index++;
                const date = queue[currentIndex];
                try {
                    await this.fetchDailyData(date, false, skipNutrition);
                } catch (e) {
                    console.error('prefetchDailyDates error:', date, e);
                }
                completed++;
                if (onProgress) onProgress(completed, total);
            }
        });
        await Promise.all(workers);
    }

    private async prefetchCurrentMonthDailyData(waitForAll: boolean = false, onProgress?: (done: number, total: number) => void, skipNutrition: boolean = false) {
        const dates = this.getAvailableMealDates();
        if (dates.length === 0) return;
        if (waitForAll) {
            await this.prefetchDailyDates(dates, 4, onProgress, skipNutrition);
            return;
        }
        void this.prefetchDailyDates(dates, 4, undefined, skipNutrition);
    }

    public async onCalendarDayClick(item: any) {
        if (!item.day) return;
        this.selectedDate = item.date;
        this.mode = 'daily';
        this.showForm = false;
        this.editingMealId = null;
        if (this.dailyCache[this.selectedDate]) {
            this.applyDailyData(this.dailyCache[this.selectedDate]);
        } else {
            this.seedDailyFromMonthly(this.selectedDate);
        }
        await this.service.render();
        await this.loadDaily();
        await this.service.render();
    }

    private async loadDaily() {
        const reqId = ++this._dailyRequestId;
        this.dailyLoading = true;
        const cached = this.dailyCache[this.selectedDate];
        if (cached) {
            this.applyDailyData(cached);
            // 영양 데이터가 없으면 (skip_nutrition으로 프리패치된 경우) 풀 데이터 재요청
            const hasNutrition = cached.nutrition_by_age && Object.keys(cached.nutrition_by_age).length > 0;
            if (!hasNutrition) {
                const freshData = await this.fetchDailyData(this.selectedDate, true);
                if (reqId !== this._dailyRequestId) return;
                if (freshData) this.applyDailyData(freshData);
            }
            this.dailyLoading = false;
            return;
        }
        const data = await this.fetchDailyData(this.selectedDate);
        if (reqId !== this._dailyRequestId) return; // 새 요청이 들어왔으면 무시
        if (data) {
            this.applyDailyData(data);
        }
        this.dailyLoading = false;
    }

    public async prevMonth() {
        const [y, m] = this.selectedMonth.split('-').map(Number);
        const d = new Date(y, m - 2, 1);
        this.selectedMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        this.dailyCache = {};
        this.dailyFetchPromises = {};
        await this.loadMonthly();
        await this.loadMealFiles();
        await this.prefetchCurrentMonthDailyData(false, undefined, true);
        await this.service.render();
    }

    public async nextMonth() {
        const [y, m] = this.selectedMonth.split('-').map(Number);
        const d = new Date(y, m, 1);
        this.selectedMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        this.dailyCache = {};
        this.dailyFetchPromises = {};
        await this.loadMonthly();
        await this.loadMealFiles();
        await this.prefetchCurrentMonthDailyData(false, undefined, true);
        await this.service.render();
    }

    public async prevDay() {
        const targetDate = this.getAdjacentMealDate('prev');
        if (!targetDate) return;
        this.selectedDate = targetDate;
        this.editingMealId = null;
        if (this.dailyCache[this.selectedDate]) {
            this.applyDailyData(this.dailyCache[this.selectedDate]);
        } else {
            this.seedDailyFromMonthly(this.selectedDate);
        }
        await this.service.render();
        await this.loadDaily();
        await this.service.render();
    }

    public async nextDay() {
        const targetDate = this.getAdjacentMealDate('next');
        if (!targetDate) return;
        this.selectedDate = targetDate;
        this.editingMealId = null;
        if (this.dailyCache[this.selectedDate]) {
            this.applyDailyData(this.dailyCache[this.selectedDate]);
        } else {
            this.seedDailyFromMonthly(this.selectedDate);
        }
        await this.service.render();
        await this.loadDaily();
        await this.service.render();
    }

    public async toggleForm() {
        this.showForm = !this.showForm;
        this.newMealType = '점심';
        this.newMealContent = '';
        this.selectedFile = null;
        this.editingMealId = null;
        await this.service.render();
    }

    public async selectNutritionAge(age: string) {
        this.selectedNutritionAge = age;
        await this.service.render();
    }

    public onFileSelect(event: any) {
        const file = event.target?.files?.[0];
        if (file) {
            this.selectedFile = file;
        }
    }

    public getMealIcon(mealType: string): string {
        if (mealType === '점심') return '🍚';
        return '🍪';
    }

    public getThemeInfo(theme: string): any {
        if (!theme) return null;
        return this.MEAL_THEMES[theme] || { emoji: '🍽️', color: '#666' };
    }

    public getDayTheme(): string {
        if (!this.meals || this.meals.length === 0) return '';
        return this.meals[0].theme || '';
    }

    public formatMealContent(content: string): string {
        if (!content) return '';
        // 연령별 연결 메뉴 분리 표시 (백김치배추김치 → 백김치(1~2세) / 배추김치(3~5세))
        const agePairs: [string, string][] = [['백김치', '배추김치']];
        for (const [young, old] of agePairs) {
            const pattern = new RegExp(young + '\\s*' + old, 'g');
            content = content.replace(pattern, young + '(1~2\uc138)\n' + old + '(3~5\uc138)');
        }
        // {{green:텍스트}} 마커를 <span class="green-text">텍스트</span>으로 변환
        // XSS 방지: 마커 외부의 텍스트는 이스케이프
        const parts = content.split(/(\{\{green:.*?\}\})/g);
        return parts.map(part => {
            const m = part.match(/^\{\{green:(.*)\}\}$/);
            if (m) {
                const escaped = m[1].replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                return `<span class="green-text">${escaped}</span>`;
            }
            return part.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }).join('').replace(/\n/g, '<br>');
    }

    public parseMealLines(content: string): any[] {
        if (!content) return [];
        // 교사/원장 뷰: 연결 메뉴 분리 표시 (백김치배추김치 → 두 줄)
        if (this.role === 'teacher' || this.role === 'director') {
            const agePairs: [string, string][] = [['백김치', '배추김치']];
            for (const [young, old] of agePairs) {
                const pattern = new RegExp(young + '\\s*' + old, 'g');
                content = content.replace(pattern, young + '(1~2세)\n' + old + '(3~5세)');
            }
        }
        const lines = content.split('\n');
        const result: any[] = [];
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const gm = line.match(/\{\{green:(.*?)\}\}(.*)/);
            if (gm) {
                // green 마커 줄 → 이전 줄이 원본
                const sub = gm[1].trim();
                const remainder = gm[2].trim();
                if (result.length > 0) {
                    result[result.length - 1].hasSubstitute = true;
                    result[result.length - 1].substituteItem = sub;
                }
                if (remainder) {
                    result.push({ text: remainder, isGreen: false, hasSubstitute: false, substituteItem: '' });
                }
            } else {
                result.push({ text: line.trim(), isGreen: false, hasSubstitute: false, substituteItem: '' });
            }
        }
        return result.filter(r => r.text);
    }

    public isSubstituteSelected(meal: any, originalItem: string): boolean {
        if (!meal.substitute_pairs) return false;
        const pair = meal.substitute_pairs.find((p: any) => p.original === originalItem);
        return pair ? pair.is_selected : false;
    }

    public async toggleSubstitute(meal: any, originalItem: string, substituteItem: string) {
        if (this.substituteLoading) return;
        this.substituteLoading = true;
        const pair = meal.substitute_pairs?.find((p: any) => p.original === originalItem);
        const newState = pair ? !pair.is_selected : true;
        try {
            const res = await wiz.call("toggle_substitute", {
                meal_id: meal.id,
                original_item: originalItem,
                substitute_item: substituteItem,
                is_selected: String(newState)
            });
            if (res.code === 200 && pair) {
                pair.is_selected = newState;
            }
        } catch (e) {
            console.error('toggleSubstitute error:', e);
        }
        this.substituteLoading = false;
        await this.service.render();
    }

    public async saveMeal() {
        if (!this.newMealContent.trim()) return;
        const formData = new FormData();
        formData.append('meal_type', this.newMealType);
        formData.append('meal_date', this.selectedDate);
        formData.append('content', this.newMealContent);
        if (this.selectedFile) {
            formData.append('photo', this.selectedFile);
        }

        const response = await fetch('/wiz/api/page.note.meal/save_meal', {
            method: 'POST',
            body: formData
        });
        const res = await response.json();
        if (res.code === 200) {
            this.showForm = false;
            this.newMealContent = '';
            this.selectedFile = null;
            delete this.dailyCache[this.selectedDate];
            this.dailyFetchPromises = {};
            await this.loadDaily();
        }
        await this.service.render();
    }

    public async deleteMeal(id: number) {
        const res = await wiz.call("delete_meal", { id: id });
        if (res.code === 200) {
            delete this.dailyCache[this.selectedDate];
            this.dailyFetchPromises = {};
            await this.loadDaily();
        }
        await this.service.render();
    }

    // ===== 식단 수정 =====
    public async startEdit(meal: any) {
        this.editingMealId = meal.id;
        this.editMealType = meal.meal_type;
        this.editMealContent = meal.content;
        this.showForm = false;
        await this.service.render();
    }

    public async cancelEdit() {
        this.editingMealId = null;
        this.editMealType = '';
        this.editMealContent = '';
        await this.service.render();
    }

    public async updateMeal() {
        if (!this.editingMealId || !this.editMealContent.trim()) return;
        const res = await wiz.call("update_meal", {
            id: this.editingMealId,
            meal_type: this.editMealType,
            content: this.editMealContent
        });
        if (res.code === 200) {
            this.editingMealId = null;
            this.editMealType = '';
            this.editMealContent = '';
            delete this.dailyCache[this.selectedDate];
            this.dailyFetchPromises = {};
            await this.loadDaily();
        }
        await this.service.render();
    }

    // ===== HWP 파싱 (월간 식단 자동 입력) =====
    public async triggerHwpUpload() {
        if (this.hwpFileInput) {
            this.hwpFileInput.nativeElement.value = '';
            this.hwpFileInput.nativeElement.click();
        }
    }

    private startHwpProgress() {
        this.hwpProgress = 0;
        this._hwpTarget = 90;
        this._hwpStartTime = Date.now();
        this.hwpProgressLabel = '파일 업로드 중...';
        const labelStages = [
            { at: 10, label: '식단표 변환 중...' },
            { at: 25, label: '메뉴 데이터 추출 중...' },
            { at: 40, label: '알레르기 분석 중...' },
            { at: 55, label: '데이터 저장 중...' },
            { at: 70, label: '식단 정리 중...' },
        ];
        let labelIdx = 0;
        // 시간 기반 증가: elapsed/(elapsed+halfTime) × target
        // halfTime=3500 → 3초: 46%, 6초: 57%, 10초: 67%, 20초: 77%
        const halfTime = 3500;
        this._hwpProgressTimer = setInterval(async () => {
            if (this.hwpProgress < this._hwpTarget) {
                let newProgress: number;
                if (this._hwpTarget >= 100) {
                    // 완료: 빠르게 부드럽게 채움
                    const step = Math.max(1.0, (this._hwpTarget - this.hwpProgress) * 0.12);
                    newProgress = this.hwpProgress + step;
                } else {
                    // 작업 중: 시간 기반 자연 증가
                    const elapsed = Date.now() - this._hwpStartTime;
                    newProgress = this._hwpTarget * elapsed / (elapsed + halfTime);
                }
                this.hwpProgress = Math.min(Math.max(this.hwpProgress, newProgress), this._hwpTarget);
                if (labelIdx < labelStages.length && this.hwpProgress >= labelStages[labelIdx].at) {
                    this.hwpProgressLabel = labelStages[labelIdx].label;
                    labelIdx++;
                }
            }
            await this.service.render();
        }, 50);
    }

    private stopHwpTimer() {
        if (this._hwpProgressTimer) {
            clearInterval(this._hwpProgressTimer);
            this._hwpProgressTimer = null;
        }
    }

    private setHwpTarget(target: number, label: string) {
        this._hwpTarget = target;
        this.hwpProgressLabel = label;
    }

    private async setHwpProgressValue(progress: number, label?: string) {
        this.hwpProgress = Math.max(this.hwpProgress, Math.min(progress, 100));
        if (label) {
            this.hwpProgressLabel = label;
        }
        await this.service.render();
    }

    public async onHwpFileSelected(event: any) {
        const file = event.target?.files?.[0];
        if (!file) return;


        this.hwpLoading = true;
        this.startHwpProgress();
        this.setHwpTarget(10, '파일 업로드 중...');
        await this.service.render();

        const formData = new FormData();
        formData.append('file', file);

        try {
            // 1. 파일 업로드 완료
            this.setHwpTarget(30, 'HWP 변환 중...');
            const response = await fetch('/wiz/api/page.note.meal/parse_hwp_meal', {
                method: 'POST',
                body: formData
            });
            const res = await response.json();

            if (res.code === 200) {
                // 업로드 요청은 여기서 끝내고, 이후 후처리는 화면에서 계속 진행한다.
                this.stopHwpTimer();
                await this.setHwpProgressValue(35, '식단표 불러오는 중...');
                const year = res.data.year;
                const month = String(res.data.month).padStart(2, '0');
                this.selectedMonth = `${year}-${month}`;

                // 2. 월간/파일 정보 로드
                await Promise.all([this.loadMonthly(), this.loadMealFiles()]);
                await this.setHwpProgressValue(50, '식단표 정리 중...');
                this.dailyCache = {};
                this.dailyFetchPromises = {};

                this.selectedDate = this.getFirstMealDateInSelectedMonth();
                if (this.getAvailableMealDates().length > 0) {
                    this.seedDailyFromMonthly(this.selectedDate);

                    const dates = this.getAvailableMealDates();
                    const total = Math.max(dates.length, 1);
                    await this.prefetchDailyDates(
                        dates,
                        6,
                        async (done: number, progressTotal: number) => {
                            const base = 50;
                            const span = 45;
                            const ratio = progressTotal > 0 ? done / progressTotal : 1;
                            const progress = base + (span * ratio);
                            await this.setHwpProgressValue(
                                progress,
                                `영양정보 저장 중... (${done}/${progressTotal})`
                            );
                        },
                        false
                    );
                } else {
                    this.resetDailyState();
                }
                this.mode = 'calendar';
                this.showForm = false;
                this.editingMealId = null;

                // 3. 모든 작업 완료
                await this.setHwpProgressValue(100, '완료!');
                await new Promise(r => setTimeout(r, 800));
            } else {
                this.stopHwpTimer();
                this.hwpProgress = 100;
                this.hwpProgressLabel = '실패';
                await this.service.render();
                await new Promise(r => setTimeout(r, 500));
                alert(res.data?.message || '식단표 파싱에 실패했습니다.');
            }
        } catch (e) {
            this.stopHwpTimer();
            this.hwpProgress = 100;
            this.hwpProgressLabel = '실패';
            await this.service.render();
            await new Promise(r => setTimeout(r, 500));
            alert('업로드 중 오류가 발생했습니다.');
        }

        this.stopHwpTimer();
        this.hwpLoading = false;
        this.hwpProgress = 0;
        if (this.hwpFileInput) {
            this.hwpFileInput.nativeElement.value = '';
        }
        await this.service.render();
    }

    // ===== 월간 HWP 삭제 (파일 + 식단 전체 삭제) =====
    public async deleteMonthHwp() {
        if (!confirm(`${this.selectedMonth} 식단표 파일과 해당 월 식단 데이터를 모두 삭제하시겠습니까?`)) return;

        const res = await wiz.call("delete_month_hwp", { month: this.selectedMonth });
        if (res.code === 200) {
            await this.loadMonthly();
            await this.loadMealFiles();
            this.dailyCache = {};
            this.dailyFetchPromises = {};
            this.selectedDate = this.getFirstMealDateInSelectedMonth();
            this.resetDailyState();
        }
        await this.service.render();
    }

    // ===== 저장된 HWP 재파싱 (테마/초록색 텍스트 업데이트) =====
    public async reparseHwp() {
        if (!confirm('저장된 HWP 파일을 재파싱하여 테마·초록색 알레르기 표기를 업데이트합니다. 계속하시겠습니까?')) return;
        this.reparseLoading = true;
        await this.service.render();
        const res = await wiz.call("reparse_stored_hwp");
        this.reparseLoading = false;
        if (res.code === 200) {
            alert(`완료: ${res.data.message}`);
            this.dailyCache = {};
            this.dailyFetchPromises = {};
            await this.loadMonthly();
            await this.loadDaily();
            await this.prefetchCurrentMonthDailyData(false, undefined, true);
        } else {
            alert('재파싱 실패. 다시 시도해주세요.');
        }
        await this.service.render();
    }

    // ===== 식단 안내 파일 관련 =====
    private async loadMealFiles() {
        const res = await wiz.call("get_meal_files");
        if (res.code === 200) {
            this.monthFiles = res.data.month_files || [];
            this.currentMonthLabel = res.data.current_month || '';
            this.nextMonthLabel = res.data.next_month || '';
            this.mealFiles = [];
            for (const group of this.monthFiles) {
                this.mealFiles.push(...(group.files || []));
            }
            // 업로드 대상 월 옵션: 이번달 + 다음달 + 기존 월들겹치지 않게
            const monthSet = new Set<string>([this.currentMonthLabel, this.nextMonthLabel]);
            for (const group of this.monthFiles) {
                monthSet.add(group.month);
            }
            this.allUploadMonths = Array.from(monthSet).sort().reverse();
            if (!this.uploadTargetMonth) {
                this.uploadTargetMonth = this.currentMonthLabel;
            }
        }
    }

    public async onMealFileSelect(event: any) {
        const file = event.target?.files?.[0];
        if (file) {
            this.selectedMealFile = file;
            await this.service.render();
        }
    }

    public async uploadMealFile() {
        if (!this.selectedMealFile) return;
        const formData = new FormData();
        formData.append('file', this.selectedMealFile);
        formData.append('target_month', this.selectedMonth);

        const response = await fetch('/wiz/api/page.note.meal/upload_meal_file', {
            method: 'POST',
            body: formData
        });
        const res = await response.json();
        if (res.code === 200) {
            this.selectedMealFile = null;
            if (this.fileInput) {
                this.fileInput.nativeElement.value = '';
            }
            await this.loadMealFiles();
        }
        await this.service.render();
    }

    public downloadMealFile(file: any) {
        window.open(`/wiz/api/page.note.meal/serve_meal_file?id=${file.id}`, '_blank');
    }

    public async deleteMealFile(id: number) {
        const res = await wiz.call("delete_meal_file", { id: id });
        if (res.code === 200) {
            await this.loadMealFiles();
        }
        await this.service.render();
    }

    // ===== 식단 통계 =====
    private dailyCaloriesCache: any = {};

    private async loadStats() {
        const res = await wiz.call("get_stats", { month: this.selectedMonth, age: this.selectedAge });
        if (res.code === 200) {
            this.statsData = res.data;
            const ageNut = res.data.age_nutrition || {};
            this.ageNutrition = Object.entries(ageNut).map(([label, val]: [string, any]) => ({
                label, kcal: val.kcal, protein: val.protein, calcium: val.calcium
            }));
            // 선택된 연령대의 kcal을 targetKcal로 설정
            const sel = this.ageNutrition.find((a: any) => a.label === this.selectedAge);
            this.targetKcal = sel ? sel.kcal : (res.data.target_kcal || 900);
            this.dailyCaloriesCache = res.data.daily_calories || {};
            this.dailyCaloriesAll = res.data.daily_calories_all || {};
            this.buildCalorieCalendar(this.dailyCaloriesCache);
        }
    }

    public async selectAge(label: string) {
        this.selectedAge = label;
        const sel = this.ageNutrition.find((a: any) => a.label === label);
        if (sel) this.targetKcal = sel.kcal;
        // 선택된 연령대의 칼로리로 캘린더 재빌드
        const ageCals = this.dailyCaloriesAll[label] || {};
        const merged = { ...this.dailyCaloriesCache };
        // 선택된 연령의 데이터로 덮어쓰기
        for (const [date, kcal] of Object.entries(ageCals)) {
            merged[date] = kcal;
        }
        this.buildCalorieCalendar(ageCals);
        await this.service.render();
    }

    private async loadParentStats() {
        const res = await wiz.call("get_parent_stats");
        if (res.code === 200) {
            let children = res.data.children || [];
            // 원장/교사: 알레르기가 있는 아이만 표시
            if (this.role === 'director' || this.role === 'teacher') {
                children = children.filter((c: any) => c.allergy_types && c.allergy_types.length > 0);
            }
            this.parentChildren = children;
            // 첫 번째 자녀의 연령대로 자동 선택
            if (this.parentChildren.length > 0) {
                const ageGroup = this.parentChildren[0].age_group;
                if (ageGroup && ageGroup !== this.selectedAge) {
                    this.selectedAge = ageGroup;
                    const sel = this.ageNutrition.find((a: any) => a.label === ageGroup);
                    if (sel) this.targetKcal = sel.kcal;
                    this.buildCalorieCalendar(this.dailyCaloriesCache);
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
            this.statsCalendar.push({ day: 0, kcal: 0, pct: 0, status: '', ageKcals: [] });
        }

        let sufficient = 0;
        let deficient = 0;
        for (let d = 1; d <= lastDate; d++) {
            const dateStr = `${this.selectedMonth}-${String(d).padStart(2, '0')}`;
            const kcal = dailyCal[dateStr] || 0;
            const pct = this.targetKcal > 0 ? Math.round(kcal / this.targetKcal * 100) : 0;
            let status = '';
            if (kcal > 0) {
                if (pct >= 90) {
                    status = 'sufficient';
                    sufficient++;
                } else {
                    status = 'deficient';
                    deficient++;
                }
            }
            // 연령별 kcal 수집
            const ageKcals: any[] = [];
            for (const age of this.ageNutrition) {
                const ageCals = this.dailyCaloriesAll[age.label] || {};
                const ak = ageCals[dateStr] || 0;
                if (ak > 0) {
                    ageKcals.push({ label: age.label, kcal: ak });
                }
            }
            this.statsCalendar.push({ day: d, kcal, pct, status, date: dateStr, ageKcals });
        }
        this.calorieSufficient = sufficient;
        this.calorieDeficient = deficient;
    }

    private buildNutrientList() {
        const nutrients = this.aiData.nutrients || {};
        this.nutrientList = Object.entries(nutrients).map(([name, val]: [string, any]) => {
            // 새 포맷: {percent, target, status} 또는 기존 포맷: 숫자
            const percent = typeof val === 'object' ? (val.percent || 0) : val;
            const target = typeof val === 'object' ? (val.target || '') : '';
            const status = typeof val === 'object' ? (val.status || '') : '';
            return {
                name,
                percent: Math.min(percent, 100),
                target,
                status,
                sufficient: percent >= 80
            };
        });
    }

    private async loadAiAnalysis(refresh: boolean = false) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 120000);
            const formData = new FormData();
            formData.append('month', this.selectedMonth);
            formData.append('refresh', refresh ? 'true' : 'false');
            formData.append('age', this.selectedAge);
            const response = await fetch('/wiz/api/page.note.meal/get_ai_analysis', {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            const res = await response.json();
            if (res.code === 200) {
                if (res.data.cached) {
                    console.log('캐시 사용됨', res.data.cached_at || '');
                }
                this.aiData = res.data;
                this.deficientNutrients = res.data.deficient_nutrients || [];
                this.aiSummary = res.data.summary || '';
                this.aiCachedAt = res.data.cached_at || '';
                this.aiDataChanged = res.data.data_changed || false;
                this.buildNutrientList();
            } else {
                this.aiError = '분석에 실패했습니다. 다시 시도해주세요.';
            }
        } catch (e: any) {
            console.error('loadAiAnalysis error:', e);
            if (e.name === 'AbortError') {
                this.aiError = '분석 시간이 초과되었습니다. 다시 시도해주세요.';
            } else {
                this.aiError = '분석에 실패했습니다. 다시 시도해주세요.';
            }
        }
    }

    public async refreshAiAnalysis() {
        this.aiLoading = true;
        this.aiError = '';
        await this.service.render();
        try {
            await this.loadAiAnalysis(true);
        } catch (e) {
            console.error('refreshAiAnalysis error:', e);
        } finally {
            this.aiLoading = false;
            await this.service.render();
        }
    }

    private async reloadStats() {
        this.statsLoading = true;
        this.statsCalendar = [];
        this.deficientNutrients = [];
        await this.service.render();
        try {
            await Promise.all([this.loadStats(), this.loadParentStats()]);
        } catch (e) {
            console.error('reloadStats error:', e);
        } finally {
            this.statsLoading = false;
            await this.service.render();
        }
    }

    public async statsPrevMonth() {
        const [y, m] = this.selectedMonth.split('-').map(Number);
        const d = new Date(y, m - 2, 1);
        this.selectedMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        await this.reloadStats();
    }

    public async statsNextMonth() {
        const [y, m] = this.selectedMonth.split('-').map(Number);
        const d = new Date(y, m, 1);
        this.selectedMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        await this.reloadStats();
    }
}
