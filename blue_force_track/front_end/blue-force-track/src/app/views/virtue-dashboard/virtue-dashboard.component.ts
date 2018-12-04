import { Component, OnInit } from '@angular/core';
import {DataService} from '../../services/data.service';
import {Virtue} from '../../models/Virtue';

@Component({
  selector: 'app-virtue-dashboard',
  templateUrl: './virtue-dashboard.component.html',
  styleUrls: ['./virtue-dashboard.component.css']
})
export class VirtueDashboardComponent implements OnInit {

  // Line Graph Config
  lineData: any[];
  lineView: any[] = [700, 400];

  // options
  lineShowXAxis = true;
  lineShowYAxis = true;
  lineGradient = false;
  lineShowLegend = true;
  lineShowXAxisLabel = true;
  lineXAxisLabel = 'Time';
  lineShowYAxisLabel = true;
  lineYAxisLabel = '# Events in Time Range';

  lineColorScheme = {
    domain: ['#5AA454', '#A10A28', '#C7B42C', '#AAAAAA']
  };

  // line, area
  autoScale = true;
  // Bar chat config
  barData: any[];
  barView: any[] = [700, 400];

  // options
  barShowXAxis = true;
  barShowYAxis = true;
  barGradient = false;
  barShowLegend = true;
  barShowXAxisLabel = true;
  barXAxisLabel = 'Virtue';
  barShowYAxisLabel = true;
  barYAxisLabel = 'Migrations Today';

  barColorScheme = {
    domain: ['#5AA454', '#A10A28', '#C7B42C', '#AAAAAA']
  };

  // Table Config
  cols = [
    { field: 'cid', header: 'Id'},
    { field: 'cipAddress', header: 'IP Address' },
    { field: 'cstate', header: 'State' },
    { field: 'cusername', header: 'Username' },
    { field: 'croleId', header: 'Role ID' }
  ];

  tableData: Virtue[];

  constructor(private dataService: DataService) { }

  ngOnInit() {
    this.dataService.getMigrationsPerVirtue().subscribe(
      response => (
        this.barData = this.buildBarData(response)
      ));

    this.updateLineGraph(null);

    this.dataService.getVirtues().subscribe(
      virtues => (
        this.tableData = this.parseArray(virtues)));
  }

  updateLineGraph(virtue: string): any {
    if (virtue) {
      this.dataService.getMessagesPerType(virtue, "day").subscribe(
        response => (
          this.lineData = this.buildLineData(response)
        )
      );
    } else {
      this.dataService.getMessagesPerVirtue("day").subscribe(
        response => (
          this.lineData = this.buildLineData(response)
        )
      );
    }
  }

  private buildBarData(response: any): any {
    const data = [];
    for (const key in response) {
      if (response.hasOwnProperty(key)) {
        const obj = {};
        obj['name'] = key;
        obj['value'] = response[key];
        data.push(obj);
      }
    }
    return data;
  }

  private buildLineData(response: any): any {
    const data = [];
    // TODO

/*

    this.lineData = [
      {
        name: "Valor 1",
        series: [
          {
            "name": "20 Oct",
            "value": 21
          },
          {
            "name": "21 Oct",
            "value": 27
          },
          {
            name: '22 Oct',
            value: 19
          }
        ]
      },

*/

    return data;
  }

  private parseArray(virtues: Virtue[]): Virtue[] {
    for (const virtue of virtues) {
      try {
        const appIds = virtue.cappIds as any;
        virtue.cappIds = JSON.parse((appIds as string).replace(/\'/g, '\"'));
      } catch (e) {
        console.log(e);
        virtue.cappIds = ['ERROR_PROCESSING_JSON'];
      }
      try {
        const resIds = virtue.cresIds as any;
        virtue.cresIds = JSON.parse((resIds as string).replace(/\'/g, '\"'));
      } catch (e) {
        console.log(e);
        virtue.cresIds = ['ERROR_PROCESSING_JSON'];
      }
      try {
        const transIds = virtue.ctransIds as any;
        virtue.ctransIds = JSON.parse((transIds as string).replace(/\'/g, '\"'));
      } catch (e) {
        console.log(e);
        virtue.ctransIds = ['ERROR_PROCESSING_JSON'];
      }
    }
    return virtues;
  }
}
