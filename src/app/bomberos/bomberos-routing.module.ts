import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { BomberosPage } from './bomberos.page';

const routes: Routes = [
  {
    path: '',
    component: BomberosPage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class BomberosPageRoutingModule {}
