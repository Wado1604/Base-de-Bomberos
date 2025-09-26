import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-admin',
  templateUrl: './admin.page.html',
  styleUrls: ['./admin.page.scss'],
})
export class AdminPage implements OnInit {
  userName: string = '';
  userPhoto: string = 'assets/img/mono.png'; // foto por defecto

  constructor() {}

  ngOnInit() {
    // Recuperar datos desde localStorage
    const nombre = localStorage.getItem('userName');
    const foto = localStorage.getItem('userPhoto');

    if (nombre) this.userName = nombre;
    if (foto) this.userPhoto = `assets/img/${foto}`; // ruta de la imagen
  }

  goTo(section: string) {
    console.log('Ir a la sección:', section);
    // Aquí puedes navegar a la sección correspondiente
    // this.router.navigate([`/${section}`]);
  }
}


