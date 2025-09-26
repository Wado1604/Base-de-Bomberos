import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BomberosPage } from './bomberos.page';

describe('BomberosPage', () => {
  let component: BomberosPage;
  let fixture: ComponentFixture<BomberosPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(BomberosPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
