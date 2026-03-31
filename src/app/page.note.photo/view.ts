import { OnInit, ViewChild, ElementRef } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    @ViewChild('slotFileInput') slotFileInput: ElementRef;

    role: string = '';
    mode: string = 'menu';
    category: string = '';
    hasAllergy: boolean = false;

    children: any[] = [];
    selectedChild: any = null;
    targetUserId: number = 0;

    // 공용 식단표 사진 캘린더 모드
    currentYear: number = new Date().getFullYear();
    currentMonth: number = new Date().getMonth() + 1;
    publicDays: any[] = [];

    // 아이 맞춤 식단 캘린더 모드
    childDays: any[] = [];
    childYear: number = new Date().getFullYear();
    childMonth: number = new Date().getMonth() + 1;

    // 슬롯 업로드 상태 (공용/아이 공유)
    pendingSlotDate: string = '';
    pendingSlotType: string = '';
    pendingCategory: string = '';

    // 날짜 추가
    showAddDate: boolean = false;
    newDate: string = '';

    // 사진 확대 보기
    expandedSlot: any = null;

    // 코멘트
    comments: any[] = [];
    commentText: string = '';
    commentLoading: boolean = false;
    quickEmojis: string[] = ['🙏', '😋', '👍', '❤️', '😊'];
    myUserId: number = 0;

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();
        const res = await wiz.call("get_role");
        if (res.code === 200) {
            this.role = res.data.role || 'parent';
            this.hasAllergy = res.data.has_allergy || false;
            this.myUserId = res.data.user_id || 0;
        }
        await this.service.render();
    }

    public async goBack() {
        if (this.mode === 'child_calendar') {
            if (this.role === 'parent') {
                this.mode = 'menu';
            } else {
                this.mode = 'child_list';
            }
            this.selectedChild = null;
            this.targetUserId = 0;
            this.childDays = [];
            this.showAddDate = false;
            await this.service.render();
            return;
        }
        if (this.mode !== 'menu') {
            this.mode = 'menu';
            this.showAddDate = false;
            this.selectedChild = null;
            this.targetUserId = 0;
            this.publicDays = [];
            this.childDays = [];
            await this.service.render();
            return;
        }
        this.router.navigate(['/note']);
    }

    public async goPublicPhotos() {
        this.category = '공용';
        this.targetUserId = 0;
        this.mode = 'public_calendar';
        this.currentYear = new Date().getFullYear();
        this.currentMonth = new Date().getMonth() + 1;
        this.showAddDate = false;
        await this.loadPublicPhotos();
        await this.service.render();
    }

    public async goChildPhotos() {
        this.category = '아이';

        if (this.role === 'parent') {
            this.targetUserId = 0;
            this.mode = 'child_calendar';
            this.childYear = new Date().getFullYear();
            this.childMonth = new Date().getMonth() + 1;
            this.showAddDate = false;
            await this.loadChildPhotos();
        } else {
            this.mode = 'child_list';
            await this.loadChildren();
        }
        await this.service.render();
    }

    // ===== 공용 캘린더 모드 =====
    public getMonthLabel(): string {
        return `${this.currentYear}년 ${this.currentMonth}월`;
    }

    public async prevMonth() {
        this.currentMonth--;
        if (this.currentMonth < 1) {
            this.currentMonth = 12;
            this.currentYear--;
        }
        await this.loadPublicPhotos();
        await this.service.render();
    }

    public async nextMonth() {
        this.currentMonth++;
        if (this.currentMonth > 12) {
            this.currentMonth = 1;
            this.currentYear++;
        }
        await this.loadPublicPhotos();
        await this.service.render();
    }

    private async loadPublicPhotos() {
        const res = await wiz.call("get_public_photos", {
            year: this.currentYear,
            month: this.currentMonth
        });
        if (res.code === 200) {
            this.publicDays = res.data.days || [];
        }
    }

    // ===== 아이 맞춤 캘린더 모드 =====
    public getChildMonthLabel(): string {
        return `${this.childYear}년 ${this.childMonth}월`;
    }

    public async prevChildMonth() {
        this.childMonth--;
        if (this.childMonth < 1) {
            this.childMonth = 12;
            this.childYear--;
        }
        await this.loadChildPhotos();
        await this.service.render();
    }

    public async nextChildMonth() {
        this.childMonth++;
        if (this.childMonth > 12) {
            this.childMonth = 1;
            this.childYear++;
        }
        await this.loadChildPhotos();
        await this.service.render();
    }

    private async loadChildPhotos() {
        const params: any = {
            year: this.childYear,
            month: this.childMonth
        };
        if (this.targetUserId > 0) {
            params.target_user_id = this.targetUserId;
        }
        const res = await wiz.call("get_child_photos", params);
        if (res.code === 200) {
            this.childDays = res.data.days || [];
        }
    }

    // ===== 공통 슬롯 유틸 =====
    public getSlotPhotoUrl(slot: any): string {
        if (!slot.photo) return '';
        let path = slot.photo.photo_path || '';
        if (path.includes('/')) {
            path = path.split('/').pop();
        }
        return `/wiz/api/page.note.photo/serve_photo?filename=${encodeURIComponent(path)}`;
    }

    public async onSlotUploadClick(day: any, slot: any, category: string = '공용') {
        this.pendingSlotDate = day.date;
        this.pendingSlotType = slot.meal_type;
        this.pendingCategory = category;
        await this.service.render();
        setTimeout(() => {
            if (this.slotFileInput) {
                this.slotFileInput.nativeElement.value = '';
                this.slotFileInput.nativeElement.click();
            }
        }, 50);
    }

    private compressImage(file: File, maxWidth: number = 1200, quality: number = 0.85): Promise<Blob> {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => {
                let w = img.width;
                let h = img.height;
                if (w > maxWidth) {
                    const ratio = maxWidth / w;
                    w = maxWidth;
                    h = Math.round(h * ratio);
                }
                const canvas = document.createElement('canvas');
                canvas.width = w;
                canvas.height = h;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, w, h);
                canvas.toBlob(
                    (blob) => {
                        URL.revokeObjectURL(img.src);
                        if (blob) resolve(blob);
                        else reject(new Error('Compression failed'));
                    },
                    'image/jpeg',
                    quality
                );
            };
            img.onerror = () => {
                URL.revokeObjectURL(img.src);
                reject(new Error('Image load failed'));
            };
            img.src = URL.createObjectURL(file);
        });
    }

    public async onSlotFileSelected(event: any) {
        const file = event.target?.files?.[0];
        if (!file || !this.pendingSlotDate || !this.pendingSlotType) return;

        this.service.loading.show();
        try {
            const compressed = await this.compressImage(file);

            const formData = new FormData();
            formData.append('category', this.pendingCategory || '공용');
            formData.append('meal_type', this.pendingSlotType);
            formData.append('photo_date', this.pendingSlotDate);
            formData.append('title', this.pendingSlotType);
            formData.append('photo', compressed, 'photo.jpg');
            if (this.pendingCategory === '아이' && this.targetUserId > 0) {
                formData.append('target_user_id', String(this.targetUserId));
            }

            const response = await fetch('/wiz/api/page.note.photo/upload_photo', {
                method: 'POST',
                body: formData
            });
            const res = await response.json();
            if (res.code === 200) {
                if (this.pendingCategory === '아이') {
                    await this.loadChildPhotos();
                } else {
                    await this.loadPublicPhotos();
                }
            }
        } catch (e) {
            // network error
        } finally {
            this.service.loading.hide();
        }

        this.pendingSlotDate = '';
        this.pendingSlotType = '';
        this.pendingCategory = '';
        if (this.slotFileInput) {
            this.slotFileInput.nativeElement.value = '';
        }
        await this.service.render();
    }

    public async deleteSlotPhoto(slot: any, category: string = '공용') {
        if (!slot.photo) return;
        const res = await wiz.call("delete_photo", { id: slot.photo.id });
        if (res.code === 200) {
            if (category === '아이') {
                await this.loadChildPhotos();
            } else {
                await this.loadPublicPhotos();
            }
        }
        await this.service.render();
    }

    // ===== 날짜 카드 삭제 =====
    public async deleteDatePhotos(day: any, category: string) {
        // 로컬 배열에서 즉시 제거 (UI 즉시 반영)
        if (category === '아이') {
            this.childDays = this.childDays.filter((d: any) => d.date !== day.date);
        } else {
            this.publicDays = this.publicDays.filter((d: any) => d.date !== day.date);
        }
        await this.service.render();

        // 실제 사진이 있는 경우에만 서버에서 삭제 후 리로드
        const hasPhotos = day.slots && day.slots.some((s: any) => s.photo);
        if (hasPhotos) {
            const params: any = { date: day.date, category: category };
            if (category === '아이' && this.targetUserId > 0) {
                params.target_user_id = this.targetUserId;
            }
            await wiz.call("delete_date_photos", params);
            if (category === '아이') {
                await this.loadChildPhotos();
            } else {
                await this.loadPublicPhotos();
            }
            await this.service.render();
        }
    }

    // ===== 사진 확대 보기 =====
    public async openSlotPhoto(slot: any) {
        if (!slot.photo) return;
        this.expandedSlot = slot;
        this.comments = [];
        this.commentText = '';
        await this.loadComments(slot.photo.id);
        await this.service.render();
    }

    public async closeSlotPhoto() {
        this.expandedSlot = null;
        this.comments = [];
        this.commentText = '';
        await this.service.render();
    }

    private async loadComments(photoId: number) {
        const res = await wiz.call("get_comments", { photo_id: photoId });
        if (res.code === 200) {
            this.comments = res.data.comments || [];
        }
    }

    public async addComment() {
        if (!this.commentText.trim() || !this.expandedSlot?.photo) return;
        this.commentLoading = true;
        await this.service.render();

        const res = await wiz.call("add_comment", {
            photo_id: this.expandedSlot.photo.id,
            content: this.commentText.trim().substring(0, 50)
        });

        this.commentLoading = false;
        if (res.code === 200) {
            this.commentText = '';
            await this.loadComments(this.expandedSlot.photo.id);
        }
        await this.service.render();
    }

    public async deleteComment(commentId: number) {
        if (!this.expandedSlot?.photo) return;
        const res = await wiz.call("delete_comment", { comment_id: commentId });
        if (res.code === 200) {
            await this.loadComments(this.expandedSlot.photo.id);
        }
        await this.service.render();
    }

    public async addEmoji(emoji: string) {
        if (!this.expandedSlot?.photo) return;
        this.commentLoading = true;
        await this.service.render();

        const res = await wiz.call("add_comment", {
            photo_id: this.expandedSlot.photo.id,
            content: emoji
        });

        this.commentLoading = false;
        if (res.code === 200) {
            await this.loadComments(this.expandedSlot.photo.id);
        }
        await this.service.render();
    }

    // ===== 날짜 추가 (공용 + 아이 공유) =====
    public async onAddDateClick() {
        const today = new Date();
        const y = today.getFullYear();
        const m = String(today.getMonth() + 1).padStart(2, '0');
        const d = String(today.getDate()).padStart(2, '0');
        this.newDate = `${y}-${m}-${d}`;
        this.showAddDate = true;
        await this.service.render();
    }

    public async confirmAddDate() {
        if (!this.newDate) return;
        const parts = this.newDate.split('-');
        const dateStr = `${parts[0]}.${parts[1]}.${parts[2]}`;
        const isChild = this.mode === 'child_calendar';
        const days = isChild ? this.childDays : this.publicDays;

        const exists = days.some((day: any) => day.date === dateStr);
        if (!exists) {
            days.push({
                date: dateStr,
                slots: [
                    { meal_type: '오전간식', photo: null },
                    { meal_type: '점심식사', photo: null },
                    { meal_type: '오후간식', photo: null }
                ]
            });
            days.sort((a: any, b: any) => b.date.localeCompare(a.date));
        }

        const addedYear = parseInt(parts[0]);
        const addedMonth = parseInt(parts[1]);
        if (isChild) {
            if (addedYear !== this.childYear || addedMonth !== this.childMonth) {
                this.childYear = addedYear;
                this.childMonth = addedMonth;
                await this.loadChildPhotos();
                const stillExists = this.childDays.some((day: any) => day.date === dateStr);
                if (!stillExists) {
                    this.childDays.push({
                        date: dateStr,
                        slots: [
                            { meal_type: '오전간식', photo: null },
                            { meal_type: '점심식사', photo: null },
                            { meal_type: '오후간식', photo: null }
                        ]
                    });
                    this.childDays.sort((a: any, b: any) => b.date.localeCompare(a.date));
                }
            }
        } else {
            if (addedYear !== this.currentYear || addedMonth !== this.currentMonth) {
                this.currentYear = addedYear;
                this.currentMonth = addedMonth;
                await this.loadPublicPhotos();
                const stillExists = this.publicDays.some((day: any) => day.date === dateStr);
                if (!stillExists) {
                    this.publicDays.push({
                        date: dateStr,
                        slots: [
                            { meal_type: '오전간식', photo: null },
                            { meal_type: '점심식사', photo: null },
                            { meal_type: '오후간식', photo: null }
                        ]
                    });
                    this.publicDays.sort((a: any, b: any) => b.date.localeCompare(a.date));
                }
            }
        }

        this.showAddDate = false;
        this.newDate = '';
        await this.service.render();
    }

    public async cancelAddDate() {
        this.showAddDate = false;
        this.newDate = '';
        await this.service.render();
    }

    // ===== 아이 목록 =====
    private async loadChildren() {
        const res = await wiz.call("get_children_list");
        if (res.code === 200) {
            this.children = res.data.children || [];
        }
    }

    public async selectChild(child: any) {
        this.selectedChild = child;
        this.targetUserId = child.user_id;
        this.mode = 'child_calendar';
        this.childYear = new Date().getFullYear();
        this.childMonth = new Date().getMonth() + 1;
        this.showAddDate = false;
        await this.loadChildPhotos();
        await this.service.render();
    }

    public canUpload(): boolean {
        return this.role === 'teacher' || this.role === 'director';
    }

    public getChildCalendarTitle(): string {
        if (this.selectedChild) return '👶 ' + this.selectedChild.child_name + ' 맞춤 식단';
        return '👶 아이 맞춤 식단';
    }

    public getMealSlotClass(mealType: string): string {
        if (mealType === '오전간식') return 'slot-morning';
        if (mealType === '점심식사') return 'slot-lunch';
        return 'slot-afternoon';
    }
}
