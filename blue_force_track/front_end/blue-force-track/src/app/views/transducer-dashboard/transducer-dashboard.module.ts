import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TransducerDashboardComponent } from './transducer-dashboard.component';
import {NgxChartsModule} from '@swimlane/ngx-charts';
import {TableModule} from 'primeng/table';

@NgModule({
  imports: [
    CommonModule,
    NgxChartsModule,
    TableModule
  ],
  exports: [
    TransducerDashboardComponent
  ],
  declarations: [TransducerDashboardComponent]
})
export class TransducerDashboardModule { }
