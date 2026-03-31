import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    role: string = '';
    teachers: any[] = [];
    children: any[] = [];
    classes: any[] = [];

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
        } else if (res.code === 403) {
            this.router.navigate(['/note']);
            return;
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
