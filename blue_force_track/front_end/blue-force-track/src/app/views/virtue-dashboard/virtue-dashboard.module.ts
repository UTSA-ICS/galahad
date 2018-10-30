import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VirtueDashboardComponent } from './virtue-dashboard.component';
import {NgxChartsModule} from '@swimlane/ngx-charts';
import {TableModule} from 'primeng/table';

@NgModule({
  imports: [
    CommonModule,
    NgxChartsModule,
    TableModule
  ],
  exports: [
    VirtueDashboardComponent
  ],
  declarations: [VirtueDashboardComponent]
})
export class VirtueDashboardModule { }
