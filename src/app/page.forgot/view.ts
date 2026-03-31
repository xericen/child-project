import { OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    step: number = 1;
    nickname: string = '';
    email: string = '';
    newPassword: string = '';
    confirmPassword: string = '';
    codeDigits: string[] = ['', '', '', '', '', ''];
    codeComplete: boolean = false;

    constructor(public service: Service, public router: Router) {}

    public async ngOnInit() {
        await this.service.init();
        await this.service.render();
    }

    get isStep1Complete(): boolean {
        return this.nickname.length > 0 && this.email.length > 0;
    }

    get isStep3Complete(): boolean {
        return this.newPassword.length > 0 && this.newPassword === this.confirmPassword;
    }

    get fullCode(): string {
        return this.codeDigits.join('');
    }

    public trackByIndex(index: number): number {
        return index;
    }

    private checkCodeComplete() {
        this.codeComplete = this.codeDigits.every(d => /^\d$/.test(d));
    }

    private getCodeInputs(): NodeListOf<HTMLInputElement> | null {
        const wrap = document.querySelector('.code-input-wrap');
        return wrap?.querySelectorAll<HTMLInputElement>('.code-digit') || null;
    }

    public async onPasswordChange() {
        await this.service.render();
    }

    public async sendCode() {
        if (!this.isStep1Complete) return;

        const res = await wiz.call("send_code", {
            nickname: this.nickname,
            email: this.email
        });

        if (res.code === 200) {
            alert('인증코드가 이메일로 발송되었습니다.');
            this.codeDigits = ['', '', '', '', '', ''];
            this.codeComplete = false;
            this.step = 2;
        } else {
            alert(res.data?.message || '인증코드 발송에 실패했습니다.');
        }
        await this.service.render();
    }

    public async resendCode() {
        const res = await wiz.call("resend_code");

        if (res.code === 200) {
            alert('인증코드가 재전송되었습니다.');
            this.codeDigits = ['', '', '', '', '', ''];
            this.codeComplete = false;
        } else {
            alert(res.data?.message || '재전송에 실패했습니다.');
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

    public async verifyCode() {
        if (!this.codeComplete) {
            alert('인증코드 6자리를 모두 입력해주세요.');
            return;
        }

        const res = await wiz.call("verify_code", { code: this.fullCode });

        if (res.code === 200) {
            this.step = 3;
        } else {
            alert(res.data?.message || '인증코드가 올바르지 않습니다.');
        }
        await this.service.render();
    }

    public async resetPassword() {
        if (!this.isStep3Complete) return;

        const res = await wiz.call("reset_password", {
            password: this.newPassword
        });

        if (res.code === 200) {
            alert('비밀번호가 변경되었습니다. 로그인 화면으로 이동합니다.');
            this.router.navigate(['/main']);
        } else {
            alert(res.data?.message || '비밀번호 변경에 실패했습니다.');
        }
        await this.service.render();
    }

    public async prevStep() {
        if (this.step > 1) {
            this.step--;
            await this.service.render();
        }
    }

    public navigate(path: string) {
        this.router.navigate([path]);
    }
}
