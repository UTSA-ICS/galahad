import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RoleDashboardComponent } from './role-dashboard.component';
import {NgxChartsModule} from '@swimlane/ngx-charts';
import {TableModule} from 'primeng/table';

@NgModule({
  imports: [
    CommonModule,
    NgxChartsModule,
    TableModule
  ],
  exports: [
    RoleDashboardComponent
  ],
  declarations: [RoleDashboardComponent]
})
export class RoleDashboardModule { }
