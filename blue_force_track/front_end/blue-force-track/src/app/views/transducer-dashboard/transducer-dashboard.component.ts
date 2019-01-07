import { Component, OnInit } from '@angular/core';
import {DataService} from '../../services/data.service';

@Component({
  selector: 'app-transducer-dashboard',
  templateUrl: './transducer-dashboard.component.html',
  styleUrls: ['./transducer-dashboard.component.css']
})
export class TransducerDashboardComponent implements OnInit {

  // Table Config
  cols = [
    { field: 'name', header: 'Name' },
    { field: 'cid', header: 'ID' },
    { field: 'ctype', header: 'Type' },
    { field: 'cstartEnabled', header: 'Start as Enabled' },
    { field: 'cstartConfig', header: 'Starting Config' },
    { field: 'creqAccess', header: 'Resource Access' }
  ];

  tableData: any[];

  constructor(private dataService: DataService) { }

  ngOnInit() {
    this.dataService.getTransducers().subscribe(
      transducers => (
        this.tableData = transducers
      ));
  }

}
