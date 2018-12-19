import { Component, OnDestroy, OnInit } from '@angular/core';
import {DataService} from '../../services/data.service';
import {Virtue} from '../../models/Virtue';
import { interval } from 'rxjs/index';

@Component({
  selector: 'app-virtue-dashboard',
  templateUrl: './virtue-dashboard.component.html',
  styleUrls: ['./virtue-dashboard.component.css']
})
export class VirtueDashboardComponent implements OnInit, OnDestroy {

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

  private alive: boolean;
  private selectedVirtue: string;
   selectedVirtueObject: Virtue;

  constructor(private dataService: DataService) {
    this.alive = true;
  }

  ngOnInit() {
    this.dataService.getMigrationsPerVirtue().subscribe(
      response => (
        this.barData = this.buildBarData(response)
      ));

    this.selectedVirtue = null;
    this.updateLineGraph(this.selectedVirtue);

    this.dataService.getVirtues().subscribe(
      virtues => (
        this.tableData = this.parseArray(virtues))
    );

    // Refresh every 10 seconds
    const secondsCounter = interval(10000);
    secondsCounter.subscribe(n =>
      this.dataService.getMigrationsPerVirtue().subscribe(
        response => (
          this.barData = this.buildBarData(response)
        ))
    );
    secondsCounter.subscribe(n =>
      this.updateLineGraph(this.selectedVirtue)
    );
    secondsCounter.subscribe(n =>
      this.dataService.getVirtues()
        .subscribe(virtues => (
          this.tableData = this.parseArray(virtues)
      ))
    );
  }

  ngOnDestroy() {
    this.alive = false;
  }

  updateLineGraph(virtue: string): any {
    this.selectedVirtue = virtue;
    if (virtue) {
      this.dataService.getMessagesPerType(virtue, "hour").subscribe(
        response => (
          this.lineData = this.buildLineData(response, 'group_by_type')
        )
      );
    } else {
      this.dataService.getMessagesPerVirtue("hour").subscribe(
        response => (
          this.lineData = this.buildLineData(response, 'group_by_virtue')
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

  private buildLineData(response: any, group_name: string): any {
    var data = [];
    var top_level_buckets = response['aggregations'][group_name]['buckets'];
    for (var i = 0; i < top_level_buckets.length; i++) {
      var bucket = top_level_buckets[i];
      const obj = {};
      obj['name'] = bucket['key'];
      const series = [];
      var time_buckets = bucket['group_by_time']['buckets'];
      for (var j = 0; j < time_buckets.length; j++) {
        var time_bucket = time_buckets[j]
        const timeObj = {};
        timeObj['name'] = time_bucket['key_as_string'];
        timeObj['value'] = time_bucket['doc_count'];
        series.push(timeObj);
      }
      obj['series'] = series;
      data.push(obj);
    }

    return data;
  }

  private parseArray(virtues: Virtue[]): Virtue[] {
    for (const virtue of virtues) {
      try {
        let appIds = virtue.cappIds as any;
        appIds = (appIds as string).replace(/u\'/g, '\'');
        virtue.cappIds = JSON.parse((appIds as string).replace(/\'/g, '\"'));
      } catch (e) {
        console.log(e);
        virtue.cappIds = ['ERROR_PROCESSING_JSON'];
      }
      try {
        let resIds = virtue.cresIds as any;
        resIds = (resIds as string).replace(/u\'/g, '\'');
        virtue.cresIds = JSON.parse((resIds as string).replace(/\'/g, '\"'));
      } catch (e) {
        console.log(e);
        virtue.cresIds = ['ERROR_PROCESSING_JSON'];
      }
      try {
        let transIds = virtue.ctransIds as any;
        transIds = (transIds as string).replace(/u\'/g, '\'');
        virtue.ctransIds = JSON.parse((transIds as string).replace(/\'/g, '\"'));
      } catch (e) {
        console.log(e);
        virtue.ctransIds = ['ERROR_PROCESSING_JSON'];
      }
    }
    return virtues;
  }

  onRowSelect(event) {
    console.log(event);
    this.updateLineGraph(event.data.cid);
  }

  onRowUnselect(event) {
    console.log(event);
    this.updateLineGraph(null);
  }
}
