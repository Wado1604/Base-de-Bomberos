import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { BomberosPageRoutingModule } from './bomberos-routing.module';

import { BomberosPage } from './bomberos.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    BomberosPageRoutingModule
  ],
  declarations: [BomberosPage]
})
export class BomberosPageModule {}
