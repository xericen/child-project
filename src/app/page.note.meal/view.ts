import { OnInit, ViewChild, ElementRef } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    @ViewChild('fileInput') fileInput: ElementRef;
    @ViewChild('hwpFileInput') hwpFileInput: ElementRef;

    role: string = '';
    mode: string = 'menu';
    selectedDate: string = '';
    selectedMonth: string = '';
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

    // 부모용 맞춤 통계
    parentData: any = {};
    parentChildren: any[] = [];
    allergyExpanded: boolean = false;

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
        await this.service.render();
    }

    private formatDate(d: Date): string {
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const dd = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${dd}`;
    }

    public async goBack() {
        if (this.mode !== 'menu') {
            this.mode = 'menu';
            this.showForm = false;
            this.editingMealId = null;
            await this.service.render();
            return;
        }
        this.router.navigate(['/note']);
    }

    public async goMonthly() {
        this.mode = 'monthly';
        this.showForm = false;
        await this.loadMonthly();
        await this.service.render();
    }

    public goNutritionDashboard() {
        this.router.navigateByUrl('/note/meal/nutrition');
    }

    public async goDaily() {
        this.mode = 'daily';
        this.showForm = false;
        this.editingMealId = null;
        await this.loadDaily();
        await this.service.render();
    }

    public async goStats() {
        this.mode = 'stats';
        this.statsLoading = true;
        this.aiLoading = false;
        this.aiError = '';
        this.aiData = {};
        this.nutrientList = [];
        this.deficientNutrients = [];
        this.aiSummary = '';
        this.parentChildren = [];
        await this.service.render();
        try {
            await this.loadStats();
            await this.loadParentStats();
            this.statsLoading = false;
            await this.service.render();
            if (this.statsData.total_meals > 0) {
                this.aiLoading = true;
                await this.service.render();
                await this.loadAiAnalysis();
            }
        } catch (e) {
            console.error('goStats error:', e);
        } finally {
            this.statsLoading = false;
            this.aiLoading = false;
            await this.service.render();
        }
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
            this.calendarDays.push({ day: '', hasMeal: false });
        }
        for (let d = 1; d <= lastDate; d++) {
            const dateStr = `${this.selectedMonth}-${String(d).padStart(2, '0')}`;
            const dayMeals = this.monthlyMeals[dateStr] || [];
            const theme = dayMeals.length > 0 ? (dayMeals[0].theme || '') : '';
            this.calendarDays.push({
                day: d,
                date: dateStr,
                hasMeal: dayMeals.length > 0,
                theme: theme
            });
        }
    }

    public async onCalendarDayClick(item: any) {
        if (!item.day) return;
        this.selectedDate = item.date;
        this.mode = 'daily';
        this.showForm = false;
        this.editingMealId = null;
        await this.loadDaily();
        await this.service.render();
    }

    private async loadDaily() {
        const res = await wiz.call("get_daily", { date: this.selectedDate });
        if (res.code === 200) {
            this.meals = res.data.meals || [];
        }
    }

    public async prevMonth() {
        const [y, m] = this.selectedMonth.split('-').map(Number);
        const d = new Date(y, m - 2, 1);
        this.selectedMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        await this.loadMonthly();
        await this.service.render();
    }

    public async nextMonth() {
        const [y, m] = this.selectedMonth.split('-').map(Number);
        const d = new Date(y, m, 1);
        this.selectedMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        await this.loadMonthly();
        await this.service.render();
    }

    public async prevDay() {
        const d = new Date(this.selectedDate);
        d.setDate(d.getDate() - 1);
        this.selectedDate = this.formatDate(d);
        this.editingMealId = null;
        await this.loadDaily();
        await this.service.render();
    }

    public async nextDay() {
        const d = new Date(this.selectedDate);
        d.setDate(d.getDate() + 1);
        this.selectedDate = this.formatDate(d);
        this.editingMealId = null;
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
            await this.loadDaily();
        }
        await this.service.render();
    }

    public async deleteMeal(id: number) {
        const res = await wiz.call("delete_meal", { id: id });
        if (res.code === 200) {
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

    public async onHwpFileSelected(event: any) {
        const file = event.target?.files?.[0];
        if (!file) return;

        this.hwpLoading = true;
        await this.service.render();

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/wiz/api/page.note.meal/parse_hwp_meal', {
                method: 'POST',
                body: formData
            });
            const res = await response.json();
            if (res.code === 200) {
                const year = res.data.year;
                const month = String(res.data.month).padStart(2, '0');
                this.selectedMonth = `${year}-${month}`;
                await this.loadMonthly();
            } else {
                alert(res.data?.message || '식단표 파싱에 실패했습니다.');
            }
        } catch (e) {
            alert('업로드 중 오류가 발생했습니다.');
        }

        this.hwpLoading = false;
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
            await this.loadMonthly();
            await this.loadDaily();
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
        formData.append('target_month', this.uploadTargetMonth);

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
            this.buildCalorieCalendar(this.dailyCaloriesCache);
        }
    }

    public async selectAge(label: string) {
        this.selectedAge = label;
        const sel = this.ageNutrition.find((a: any) => a.label === label);
        if (sel) this.targetKcal = sel.kcal;
        await this.loadStats();
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
                if (pct >= 90) {
                    status = 'sufficient';
                    sufficient++;
                } else {
                    status = 'deficient';
                    deficient++;
                }
            }
            this.statsCalendar.push({ day: d, kcal, pct, status, date: dateStr });
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
        this.aiLoading = false;
        this.aiError = '';
        this.aiData = {};
        this.nutrientList = [];
        this.deficientNutrients = [];
        this.aiSummary = '';
        this.statsCalendar = [];
        await this.service.render();
        try {
            await this.loadStats();
            this.statsLoading = false;
            await this.service.render();
            if (this.statsData.total_meals > 0) {
                this.aiLoading = true;
                await this.service.render();
                await this.loadAiAnalysis();
            }
        } catch (e) {
            console.error('reloadStats error:', e);
        } finally {
            this.statsLoading = false;
            this.aiLoading = false;
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
