import { Injectable } from '@angular/core';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {Observable} from 'rxjs/index';
import {Virtue} from '../models/Virtue';
import {Role} from '../models/Role';
import {User} from '../models/User';
import {Resource} from '../models/Resource';

@Injectable({
  providedIn: 'root'
})
export class DataService {
  private baseUrl = 'http://localhost:3000'

  // API URL's
  private virtuesUrl = '/virtues';
  private rolesUrl = '/roles';
  private valorsUrl = '/valors';
  private usersUrl = '/users';
  private resourcesUrl = '/resources';

  constructor(private http: HttpClient) { }

  getValors(): Observable<any> {
    return this.http.get(this.baseUrl + this.valorsUrl);
  }

  getVirtues(): Observable<Virtue[]> {
    return this.http.get<Virtue[]>(this.baseUrl + this.virtuesUrl);
  }

  getRoles(): Observable<Role[]> {
    return this.http.get<Role[]>(this.baseUrl + this.rolesUrl);
  }

  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(this.baseUrl + this.usersUrl);
  }

  getResources(): Observable<Resource[]> {
    return this.http.get<Resource[]>(this.baseUrl + this.resourcesUrl);
  }
}
