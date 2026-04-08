import { OnInit, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit, AfterViewChecked {
    step: number = 1;
    nickname: string = '';
    phone: string = '';
    selectedRole: string = '';
    childName: string = '';
    className: string = '';
    email: string = '';
    password: string = '';
    codeDigits: string[] = ['', '', '', '', '', ''];
    codeComplete: boolean = false;
    serverName: string = '';

    birthYear: number = 2020;
    birthMonth: number = 1;
    birthDay: number = 1;

    years: number[] = [];
    months: number[] = [];
    days: number[] = [];

    private wheelScrolled: boolean = false;

    @ViewChild('yearWheel') yearWheel: ElementRef;
    @ViewChild('monthWheel') monthWheel: ElementRef;
    @ViewChild('dayWheel') dayWheel: ElementRef;

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();

        // 서버 정보 확인 — 없으면 서버 선택 페이지로
        const res = await wiz.call("get_server_info");
        if (res.code === 200) {
            this.serverName = res.data.server_name || '';
        } else {
            this.router.navigate(['/']);
            return;
        }

        const currentYear = new Date().getFullYear();
        for (let y = currentYear; y >= 2000; y--) this.years.push(y);
        for (let m = 1; m <= 12; m++) this.months.push(m);
        this.updateDays();
        await this.service.render();
    }

    ngAfterViewChecked() {
        if (this.step === 1 && this.selectedRole === 'parent' && !this.wheelScrolled && this.yearWheel) {
            this.scrollToSelected();
            this.wheelScrolled = true;
        }
        if (this.step !== 1 || this.selectedRole !== 'parent') {
            this.wheelScrolled = false;
        }
    }

    private scrollToSelected() {
        setTimeout(() => {
            this.scrollWheelTo(this.yearWheel, this.years.indexOf(this.birthYear));
            this.scrollWheelTo(this.monthWheel, this.months.indexOf(this.birthMonth));
            this.scrollWheelTo(this.dayWheel, this.days.indexOf(this.birthDay));
        }, 50);
    }

    private scrollWheelTo(ref: ElementRef, index: number) {
        if (!ref || !ref.nativeElement || index < 0) return;
        const itemH = 36;
        ref.nativeElement.scrollTop = index * itemH;
    }

    public async selectRole(role: string) {
        this.selectedRole = role;
        await this.service.render();
    }

    public formatPhone() {
        const digits = this.phone.replace(/\D/g, '').slice(0, 11);
        if (digits.length <= 3) {
            this.phone = digits;
        } else if (digits.length <= 7) {
            this.phone = digits.slice(0, 3) + '-' + digits.slice(3);
        } else {
            this.phone = digits.slice(0, 3) + '-' + digits.slice(3, 7) + '-' + digits.slice(7);
        }
    }

    get isValidPhone(): boolean {
        if (this.phone.length === 0) return true;
        return /^010-\d{4}-\d{4}$/.test(this.phone);
    }

    get isValidEmail(): boolean {
        if (this.email.length === 0) return false;
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.email);
    }

    public async selectDate(type: string, value: number) {
        if (type === 'year') this.birthYear = value;
        else if (type === 'month') this.birthMonth = value;
        else if (type === 'day') this.birthDay = value;

        if (type === 'year' || type === 'month') this.updateDays();
        await this.service.render();
    }

    private updateDays() {
        const daysInMonth = new Date(this.birthYear, this.birthMonth, 0).getDate();
        this.days = [];
        for (let d = 1; d <= daysInMonth; d++) this.days.push(d);
        if (this.birthDay > daysInMonth) this.birthDay = daysInMonth;
    }

    get isStep1Complete(): boolean {
        if (this.nickname.length === 0 || this.selectedRole.length === 0) return false;
        if (!this.isValidPhone) return false;
        if (this.selectedRole === 'parent') {
            return this.childName.length > 0 && this.className.length > 0;
        }
        if (this.selectedRole === 'teacher') {
            return this.className.length > 0;
        }
        return true;
    }

    get isStep2Complete(): boolean {
        return this.isValidEmail && this.password.length > 0;
    }

    private checkCodeComplete() {
        this.codeComplete = this.codeDigits.every(d => /^\d$/.test(d));
    }

    get fullCode(): string {
        return this.codeDigits.join('');
    }

    public trackByIndex(index: number): number {
        return index;
    }

    private getCodeInputs(): NodeListOf<HTMLInputElement> | null {
        const wrap = document.querySelector('.code-input-wrap');
        return wrap?.querySelectorAll<HTMLInputElement>('.code-digit') || null;
    }

    public async goStep2() {
        if (!this.isStep1Complete) return;
        this.step = 2;
        await this.service.render();
    }

    public async sendCode() {
        if (!this.isStep2Complete) return;

        const params: any = {
            email: this.email,
            password: this.password,
            nickname: this.nickname,
            phone: this.phone,
            role: this.selectedRole
        };

        if (this.selectedRole === 'parent') {
            params.child_name = this.childName;
            params.child_birth_date = `${this.birthYear}-${String(this.birthMonth).padStart(2, '0')}-${String(this.birthDay).padStart(2, '0')}`;
            params.class_name = this.className + '반';
        }

        if (this.selectedRole === 'teacher') {
            params.class_name = this.className + '반';
        }

        const res = await wiz.call("send_code", params);

        if (res.code === 200) {
            alert('인증코드가 이메일로 발송되었습니다.');
            this.codeDigits = ['', '', '', '', '', ''];
            this.codeComplete = false;
            this.step = 3;
        } else {
            alert(res.data?.message || '인증코드 발송에 실패했습니다.');
        }
        await this.service.render();
    }

    public async resendCode() {
        const res = await wiz.call("resend_code");

        if (res.code === 200) {
            alert('새 인증코드가 이메일로 발송되었습니다.');
            this.codeDigits = ['', '', '', '', '', ''];
            this.codeComplete = false;
        } else {
            alert(res.data?.message || '인증코드 재전송에 실패했습니다.');
        }
        await this.service.render();
    }

    public async onCodeKeydown(event: KeyboardEvent, index: number) {
        if (/^\d$/.test(event.key)) {
            event.preventDefault();
            this.codeDigits[index] = event.key;
            this.checkCodeComplete();

            if (index < 5) {
                await this.service.render();
                const boxes = this.getCodeInputs();
                if (boxes && boxes[index + 1]) {
                    boxes[index + 1].focus();
                }
            } else {
                await this.service.render();
            }
            return;
        }

        if (event.key === 'Backspace') {
            event.preventDefault();
            if (this.codeDigits[index]) {
                this.codeDigits[index] = '';
                this.checkCodeComplete();
                await this.service.render();
            } else if (index > 0) {
                this.codeDigits[index - 1] = '';
                this.checkCodeComplete();
                await this.service.render();
                const boxes = this.getCodeInputs();
                if (boxes && boxes[index - 1]) {
                    boxes[index - 1].focus();
                }
            }
            return;
        }

        if (event.key.length === 1) {
            event.preventDefault();
        }
    }

    public async onCodePaste(event: ClipboardEvent) {
        event.preventDefault();
        const paste = event.clipboardData?.getData('text') || '';
        const digits = paste.replace(/\D/g, '').slice(0, 6);
        for (let i = 0; i < 6; i++) {
            this.codeDigits[i] = digits[i] || '';
        }
        this.checkCodeComplete();
        await this.service.render();
    }

    public async prevStep() {
        if (this.step > 1) {
            this.step--;
            await this.service.render();
        }
    }

    public async verifyCode() {
        if (!this.codeComplete) {
            alert('인증코드 6자리를 모두 입력해주세요.');
            return;
        }

        const res = await wiz.call("verify_code", { invite_code: this.fullCode });

        if (res.code === 200) {
            alert('회원가입이 완료되었습니다!\n원장의 승인 후 로그인할 수 있습니다.');
            this.router.navigate(['/main']);
        } else {
            alert(res.data?.message || '인증코드가 올바르지 않습니다.');
        }
        await this.service.render();
    }

    public navigate(path: string) {
        this.router.navigate([path]);
    }
}
