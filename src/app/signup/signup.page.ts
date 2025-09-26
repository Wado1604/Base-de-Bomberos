import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController } from '@ionic/angular';

@Component({
  selector: 'app-signup',
  templateUrl: './signup.page.html',
  styleUrls: ['./signup.page.scss'],
})
export class SignupPage {
  nombre: string = '';
  apellido: string = '';
  fechaNacimiento: string = '';
  email: string = '';
  password: string = '';
  confirmPassword: string = '';

  constructor(private router: Router, private alertCtrl: AlertController) {}

  async signup() {
    if (!this.nombre || !this.apellido || !this.fechaNacimiento || !this.email || !this.password || !this.confirmPassword) {
      this.showAlert('Error', 'Por favor, completa todos los campos');
      return;
    }

    if (this.password !== this.confirmPassword) {
      this.showAlert('Error', 'Las contraseñas no coinciden');
      return;
    }

    const user = {
      nombre: this.nombre,
      apellido: this.apellido,
      fechaNacimiento: this.fechaNacimiento,
      email: this.email,
      password: this.password
    };

    localStorage.setItem('user_' + this.email, JSON.stringify(user));

    this.showAlert('Éxito', 'Usuario registrado correctamente');

    // Redirige al Admin después de registrarse
    this.router.navigate(['/admin']);
  }

  async showAlert(header: string, message: string) {
    const alert = await this.alertCtrl.create({
      header,
      message,
      buttons: ['OK'],
    });
    await alert.present();
  }
}

