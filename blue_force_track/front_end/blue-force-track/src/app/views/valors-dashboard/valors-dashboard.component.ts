import { Component, OnInit } from '@angular/core';
import {DataService} from '../../services/data.service';

@Component({
  selector: 'app-valors-dashboard',
  templateUrl: './valors-dashboard.component.html',
  styleUrls: ['./valors-dashboard.component.css']
})
export class ValorsDashboardComponent implements OnInit {

  // Line Graph Config
  lineData: any[];
  lineView: any[] = [700, 400];

  // options
  lineShowXAxis = true;
  lineShowYAxis = true;
  lineGradient = false;
  lineShowLegend = true;
  lineShowXAxisLabel = true;
  lineXAxisLabel = 'Valors';
  lineShowYAxisLabel = true;
  lineYAxisLabel = 'Events Per Day';

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
  barXAxisLabel = 'Valor';
  barShowYAxisLabel = true;
  barYAxisLabel = 'Virtues';

  barColorScheme = {
    domain: ['#5AA454', '#A10A28', '#C7B42C', '#AAAAAA']
  };

  // Table Config
  cols = [
    { field: 'address', header: 'IP' },
    { field: 'guestnet', header: 'Guest Network' },
    { field: 'host', header: 'Host' }
  ];

  tableData: any[];

  // Line Gauge Config
  gaugeValue: number;
  gaugePreviousValue: number;
  gaugeView: any[] = [350, 150];
  gaugeUnits = 'System utilization';
  gaugeColorScheme = {
    domain: ['#5AA454', '#A10A28', '#C7B42C', '#AAAAAA']
  };


  constructor(private data: DataService) { }

  ngOnInit() {
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
      {
        "name": "Valor 2",
        "series": [
          {
            "name": "20 Oct",
            "value": 12
          },
          {
            "name": "21 Oct",
            "value": 7
          },
          {
            name: '22 Oct',
            value: 17
          }
        ]
      },

      {
        "name": "Valor 3",
        "series": [
          {
            "name": "20 Oct",
            "value": 6
          },
          {
            "name": "21 Oct",
            "value": 9
          },
          {
            name: '22 Oct',
            value: 4
          }
        ]
      }
    ];

    this.data.getVirtuesPerValor().subscribe(
      response => (
        this.barData = this.buildBarData(response)
      )
    );

    this.data.getValors().subscribe(
      valors => this.tableData = valors
    );

    this.gaugeValue = 67;
    this.gaugePreviousValue = 85;
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

  onSelect(event) {
    console.log(event);
  }

}
