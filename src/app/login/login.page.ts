import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController } from '@ionic/angular';

interface User {
  firstName: string;
  lastName: string;
  birthDate: string;
  email: string;
  password: string;
}

@Component({
  selector: 'app-login',
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.scss'],
})
export class LoginPage {
  // campos comunes
  email = '';
  password = '';

  // registro
  firstName = '';
  lastName = '';
  birthDate = '';
  confirmPassword = '';

  // estados UI
  isRegister = false;
  showPasswordLogin = false;
  showPasswordRegister = false;

  constructor(private router: Router, private alertCtrl: AlertController) {}

  // alterna entre login y registro
  toggleForm() {
    this.isRegister = !this.isRegister;
    // limpiar contraseñas visibles
    this.showPasswordLogin = false;
    this.showPasswordRegister = false;
  }

  togglePassword(context: 'login' | 'register') {
    if (context === 'login') this.showPasswordLogin = !this.showPasswordLogin;
    else this.showPasswordRegister = !this.showPasswordRegister;
  }

  // Lógica de login: busca en localStorage user_<email>
  async login() {
    if (!this.email || !this.password) {
      return this.showAlert('Error', 'Ingresa correo y contraseña.');
    }

    const key = 'user_' + this.email.toLowerCase();
    const stored = localStorage.getItem(key);
    if (!stored) {
      return this.showAlert('Error', 'Usuario no encontrado. Comprueba el correo o regístrate.');
    }

    const user: User = JSON.parse(stored);
    if (user.password !== this.password) {
      return this.showAlert('Error', 'Contraseña incorrecta.');
    }

    // Guardar usuario actual (opcional)
    localStorage.setItem('currentUser', JSON.stringify({ email: user.email, firstName: user.firstName, lastName: user.lastName }));

    // Redirigir al admin
    this.router.navigate(['/admin']);
  }

  // Registro: valida y guarda
  async register() {
    // validaciones básicas
    if (!this.firstName || !this.lastName || !this.birthDate || !this.email || !this.password || !this.confirmPassword) {
      return this.showAlert('Error', 'Completa todos los campos.');
    }

    if (this.password !== this.confirmPassword) {
      return this.showAlert('Error', 'Las contraseñas no coinciden.');
    }

    const emailKey = 'user_' + this.email.toLowerCase();
    if (localStorage.getItem(emailKey)) {
      return this.showAlert('Error', 'Ya existe un usuario con ese correo.');
    }

    const user: User = {
      firstName: this.firstName,
      lastName: this.lastName,
      birthDate: this.birthDate,
      email: this.email.toLowerCase(),
      password: this.password,
    };

    localStorage.setItem(emailKey, JSON.stringify(user));
    localStorage.setItem('currentUser', JSON.stringify({ email: user.email, firstName: user.firstName, lastName: user.lastName }));

    await this.showAlert('Éxito', 'Usuario registrado correctamente.');

    // redirigir al admin
    this.router.navigate(['/admin']);
  }

  // alerta reusable
  private async showAlert(header: string, message: string) {
    const a = await this.alertCtrl.create({
      header,
      message,
      buttons: ['OK'],
    });
    await a.present();
  }

  // función de ejemplo para recuperar contraseña (puedes personalizar)
  async forgotPassword() {
    const alert = await this.alertCtrl.create({
      header: 'Recuperar contraseña',
      inputs: [{ name: 'email', type: 'email', placeholder: 'Tu correo' }],
      buttons: [
        { text: 'Cancelar', role: 'cancel' },
        {
          text: 'Enviar',
          handler: (data) => {
            if (!data.email) {
              this.showAlert('Error', 'Ingresa tu correo primero.');
              return false;
            }
            // aquí podrías implementar envío real
            this.showAlert('Enviado', 'Si existe una cuenta, se enviaron las instrucciones.');
            return true;
          },
        },
      ],
    });
    await alert.present();
  }
}
