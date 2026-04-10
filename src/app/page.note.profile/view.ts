import { OnInit, ViewChild, ElementRef } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    role: string = '';
    teachers: any[] = [];
    children: any[] = [];
    classes: any[] = [];
    searchText: string = '';
    selectedTab: string = '';
    tabNames: string[] = [];
    currentClass: any = null;
    filteredTeachers: any[] = [];
    filteredChildren: any[] = [];
    uploadingChildId: number = 0;

    @ViewChild('childPhotoInput') childPhotoInput!: ElementRef<HTMLInputElement>;

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();
        await this.loadData();
        await this.service.render();
    }

    private async loadData() {
        const res = await wiz.call("get_profile_data");
        if (res.code === 200) {
            this.role = res.data.role || '';
            this.teachers = (res.data.teachers || []).map((t: any) => ({ ...t, showDetail: false }));
            this.children = (res.data.children || []).map((c: any) => ({ ...c, showDetail: false }));
            this.classes = (res.data.classes || []).map((cls: any) => ({
                ...cls,
                teachers: (cls.teachers || []).map((t: any) => ({ ...t, showDetail: false })),
                children: (cls.children || []).map((c: any) => ({ ...c, showDetail: false }))
            }));
            this.buildTabs();
            this.applyFilter();
        } else if (res.code === 403) {
            this.router.navigate(['/note']);
            return;
        }
    }

    private buildTabs() {
        if (this.role === 'director') {
            this.tabNames = ['전체', ...this.classes.map((cls: any) => cls.class_name)];
        } else {
            const classSet = new Set<string>();
            for (const c of this.children) {
                classSet.add(c.class_name || '미지정');
            }
            this.tabNames = Array.from(classSet);
        }
        if (this.tabNames.length > 0 && !this.tabNames.includes(this.selectedTab)) {
            this.selectedTab = this.tabNames[0];
        }
    }

    public async selectTab(tab: string) {
        this.selectedTab = tab;
        this.applyFilter();
        await this.service.render();
    }

    public async onSearch() {
        this.applyFilter();
        await this.service.render();
    }

    private applyFilter() {
        const q = (this.searchText || '').trim().toLowerCase();
        if (this.role === 'director') {
            if (this.selectedTab === '전체') {
                this.currentClass = null;
                let allTeachers: any[] = [];
                let allChildren: any[] = [];
                for (const cls of this.classes) {
                    allTeachers = allTeachers.concat(cls.teachers || []);
                    allChildren = allChildren.concat(cls.children || []);
                }
                if (q) {
                    this.filteredTeachers = allTeachers.filter((t: any) =>
                        (t.name || '').toLowerCase().includes(q) || (t.phone || '').includes(q)
                    );
                    this.filteredChildren = allChildren.filter((c: any) =>
                        (c.name || '').toLowerCase().includes(q) || (c.parent_name || '').toLowerCase().includes(q) || (c.parent_phone || '').includes(q)
                    );
                } else {
                    this.filteredTeachers = allTeachers;
                    this.filteredChildren = allChildren;
                }
            } else {
                this.currentClass = this.classes.find((cls: any) => cls.class_name === this.selectedTab) || null;
                if (this.currentClass && q) {
                    this.filteredTeachers = this.currentClass.teachers.filter((t: any) =>
                        (t.name || '').toLowerCase().includes(q) || (t.phone || '').includes(q)
                    );
                    this.filteredChildren = this.currentClass.children.filter((c: any) =>
                        (c.name || '').toLowerCase().includes(q) || (c.parent_name || '').toLowerCase().includes(q) || (c.parent_phone || '').includes(q)
                    );
                } else if (this.currentClass) {
                    this.filteredTeachers = this.currentClass.teachers;
                    this.filteredChildren = this.currentClass.children;
                } else {
                    this.filteredTeachers = [];
                    this.filteredChildren = [];
                }
            }
        } else {
            const tabChildren = this.children.filter((c: any) => (c.class_name || '미지정') === this.selectedTab);
            if (q) {
                this.filteredChildren = tabChildren.filter((c: any) =>
                    (c.name || '').toLowerCase().includes(q) || (c.parent_name || '').toLowerCase().includes(q)
                );
            } else {
                this.filteredChildren = tabChildren;
            }
        }
    }

    public async toggleDetail(item: any) {
        item.showDetail = !item.showDetail;
        await this.service.render();
    }

    public goBack() {
        this.router.navigate(['/note']);
    }

    public getAllergies(child: any): string {
        if (!child.allergies || child.allergies.length === 0) return '없음';
        return child.allergies.map((a: any) => {
            if (a.allergy_type === '기타' && a.other_detail) return a.other_detail;
            return a.allergy_type;
        }).join(', ');
    }

    public getProfilePhotoUrl(filename: string): string {
        if (!filename) return '';
        return `/wiz/api/page.note.profile/serve_profile_photo?filename=${filename}&t=${Date.now()}`;
    }

    public triggerChildPhotoUpload(child: any) {
        this.uploadingChildId = child.id;
        if (this.childPhotoInput) {
            this.childPhotoInput.nativeElement.click();
        }
    }

    public async onChildPhotoSelected(event: any) {
        const file = event.target?.files?.[0];
        if (!file || !this.uploadingChildId) return;

        const formData = new FormData();
        formData.append('photo', file);
        formData.append('child_id', String(this.uploadingChildId));

        try {
            const response = await fetch(`/wiz/api/page.note.profile/upload_child_photo`, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            });
            const result = await response.json();
            if (result.code === 200) {
                await this.loadData();
            } else {
                alert(result.data?.message || '업로드에 실패했습니다.');
            }
        } catch (e) {
            alert('업로드 중 오류가 발생했습니다.');
        }

        this.uploadingChildId = 0;
        event.target.value = '';
        await this.service.render();
    }

    public async deleteTeacher(teacher: any) {
        if (!confirm(`${teacher.name} 교사를 삭제하시겠습니까?`)) return;
        const res = await wiz.call("delete_teacher", { teacher_id: teacher.id });
        if (res.code === 200) {
            await this.loadData();
            await this.service.render();
        } else {
            alert(res.data?.message || "삭제에 실패했습니다.");
        }
    }

    public async deleteChild(child: any) {
        if (!confirm(`${child.name} 학생을 삭제하시겠습니까?`)) return;
        const res = await wiz.call("delete_child", { child_id: child.id, parent_id: child.parent_id });
        if (res.code === 200) {
            await this.loadData();
            await this.service.render();
        } else {
            alert(res.data?.message || "삭제에 실패했습니다.");
        }
    }

    public async deleteClass(className: string) {
        if (!confirm(`'${className}' 반 전체를 삭제하시겠습니까?\n\n해당 반의 교사, 학생, 학부모 정보가 모두 삭제됩니다.`)) return;
        const res = await wiz.call("delete_class", { class_name: className });
        if (res.code === 200) {
            alert(res.data?.message || "반이 삭제되었습니다.");
            await this.loadData();
            await this.service.render();
        } else {
            alert(res.data?.message || "삭제에 실패했습니다.");
        }
    }
}
