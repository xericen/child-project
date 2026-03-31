import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    step: number = 1;

    // Step 1
    directorName: string = '';
    phone: string = '';
    serverName: string = '';

    // Step 2
    email: string = '';
    password: string = '';
    passwordConfirm: string = '';

    // Step 3
    codeDigits: string[] = ['', '', '', '', '', ''];
    codeComplete: boolean = false;

    // Result
    serverCode: string = '';
    showResult: boolean = false;

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();
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

    get isStep1Complete(): boolean {
        return this.directorName.length > 0 && this.serverName.length > 0 && this.isValidPhone;
    }

    get isStep2Complete(): boolean {
        return this.isValidEmail && this.password.length > 0 && this.password === this.passwordConfirm;
    }

    public trackByIndex(index: number): number {
        return index;
    }

    private checkCodeComplete() {
        this.codeComplete = this.codeDigits.every(d => /^\d$/.test(d));
    }

    get fullCode(): string {
        return this.codeDigits.join('');
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

        const res = await wiz.call("send_code", {
            email: this.email,
            password: this.password,
            director_name: this.directorName,
            phone: this.phone,
            server_name: this.serverName + ' 어린이집'
        });

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

    public async verifyAndCreate() {
        if (!this.codeComplete) {
            alert('인증코드 6자리를 모두 입력해주세요.');
            return;
        }

        const res = await wiz.call("verify_and_create", { invite_code: this.fullCode });

        if (res.code === 200) {
            this.serverCode = res.data.server_code;
            this.showResult = true;
        } else {
            alert(res.data?.message || '인증코드가 올바르지 않습니다.');
        }
        await this.service.render();
    }

    public goLogin() {
        this.router.navigate(['/main']);
    }

    public goBack() {
        this.router.navigate(['/']);
    }
}
