export class Virtue {
  private _dn: string;
  private _cappIds: string[];
  private _objectClass: string;
  private _cipAddress: string;
  private _cid: string;
  private _cresIds: string[];
  private _cstate: string;
  private _ctransIds: string[];
  private _croleId: string;
  private _ou: string;
  private _cusername: string;


  constructor() {
  }


  get dn(): string {
    return this._dn;
  }

  set dn(value: string) {
    this._dn = value;
  }

  get cappIds(): string[] {
    return this._cappIds;
  }

  set cappIds(value: string[]) {
    this._cappIds = value;
  }

  get objectClass(): string {
    return this._objectClass;
  }

  set objectClass(value: string) {
    this._objectClass = value;
  }

  get cipAddress(): string {
    return this._cipAddress;
  }

  set cipAddress(value: string) {
    this._cipAddress = value;
  }

  get cid(): string {
    return this._cid;
  }

  set cid(value: string) {
    this._cid = value;
  }

  get cresIds(): string[] {
    return this._cresIds;
  }

  set cresIds(value: string[]) {
    this._cresIds = value;
  }

  get cstate(): string {
    return this._cstate;
  }

  set cstate(value: string) {
    this._cstate = value;
  }

  get ctransIds(): string[] {
    return this._ctransIds;
  }

  set ctransIds(value: string[]) {
    this._ctransIds = value;
  }

  get croleId(): string {
    return this._croleId;
  }

  set croleId(value: string) {
    this._croleId = value;
  }

  get ou(): string {
    return this._ou;
  }

  set ou(value: string) {
    this._ou = value;
  }

  get cusername(): string {
    return this._cusername;
  }

  set cusername(value: string) {
    this._cusername = value;
  }
}
