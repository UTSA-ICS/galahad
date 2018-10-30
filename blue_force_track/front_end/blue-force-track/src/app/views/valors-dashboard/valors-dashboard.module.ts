import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ValorsDashboardComponent } from './valors-dashboard.component';
import {NgxChartsModule} from '@swimlane/ngx-charts';
import {TableModule} from 'primeng/table';



@NgModule({
  imports: [
    CommonModule,
    NgxChartsModule,
    TableModule
  ],
  exports: [
    ValorsDashboardComponent
  ],
  declarations: [ValorsDashboardComponent]
})
export class ValorsDashboardModule { }
