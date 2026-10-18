import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const base=path.dirname(fileURLToPath(import.meta.url));
const data=JSON.parse(await fs.readFile(path.join(base,'prepared-inputs.json'),'utf8'));
const wb=Workbook.create();
const analysis=wb.worksheets.add('Analysis');
const sources=wb.worksheets.add('Sources');
const out=path.join(base,'outputs/p3-analysis');
const qa=path.join(base,'outputs/qa');
await fs.mkdir(out,{recursive:true});
await fs.mkdir(qa,{recursive:true});
assert.equal(data.jobs.length,9);
assert.equal(data.attempts.length,9);
assert.equal(data.workspaces.length,3);
for(const sheet of [analysis,sources]){
  sheet.showGridLines=false;
  sheet.getRange(sheet===analysis?'A1:L29':'A1:O16').format.font={name:'Arial',size:10,color:'#253245'};
  sheet.getRange(sheet===analysis?'A1:L29':'A1:O16').format.rowHeight=21;
  sheet.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:'#162D50'};
}
analysis.tabColor='#243F68';
analysis.getRange('A2').values=[['Job reconciliation']];
analysis.getRange('A3').values=[['UTC reporting period. Amounts are cents. n.a. means the amount is incomplete.']];
analysis.getRange('A5:B5').values=[['Period start',new Date(data.start)]];
analysis.getRange('D5:E5').values=[['End (exclusive)',new Date(data.end)]];
analysis.getRange('B5').setNumberFormat('yyyy-mm-dd');
analysis.getRange('E5').setNumberFormat('yyyy-mm-dd');
analysis.getRange('B5').format.fill='#E8F0FC';analysis.getRange('E5').format.fill='#E8F0FC';
sources.getRange('A2').values=[['Prepared source data']];
sources.getRange('A3').values=[['Source: synthetic CSV teaching case. Exact repeats removed. Rebuild after changing CSV files.']];
sources.getRange('A5:F5').values=[['Job ID','Workspace','Original timestamp','UTC timestamp','Status','Billed cents']];
sources.getRange('A6:F14').values=data.jobs.map(row=>[row.job_id,row.workspace_id,row.occurred_at ? 'raw: '+row.occurred_at : '',
  row.occurred_utc?new Date(row.occurred_utc):null,row.status,row.billed_cents]);
sources.getRange('A6:C14').setNumberFormat('@');
sources.getRange('A6:A14').setNumberFormat('0000');
sources.getRange('D6:D14').setNumberFormat('yyyy-mm-dd hh:mm');
sources.getRange('F6:F14').setNumberFormat('#,##0');
sources.getRange('H5:L5').values=[['Attempt ID','Job ID','Cost cents','Cost valid','Unassigned']];
sources.getRange('H6:J14').values=data.attempts.map(row=>[row.attempt_id,row.job_id,row.cost_cents]);
sources.getRange('H6:I14').setNumberFormat('@');
sources.getRange('I6:I14').setNumberFormat('0000');
sources.getRange('J6:L14').setNumberFormat('#,##0');
sources.getRange('K6:L14').formulas=data.attempts.map((_,i)=>{
  const r=i+6;return [`=IF(AND(ISNUMBER(J${r}),J${r}>=0),1,0)`,`=IF(COUNTIFS($A$6:$A$14,I${r})=0,1,0)`];
});
sources.getRange('N5:O5').values=[['Workspace','Plan']];
sources.getRange('N6:O8').values=data.workspaces.map(row=>[row.workspace_id,row.plan]);
sources.tables.add('A5:F14',true,'JobSource');
sources.tables.add('H5:L14',true,'AttemptSource');
sources.tables.add('N5:O8',true,'WorkspaceSource');
sources.freezePanes.freezeRows(5);
analysis.getRange('A7:C7').values=[['Metric','Value','Unit']];
analysis.getRange('A8:A16').values=[['Jobs in period'],['Completed jobs'],['Known billed subtotal'],['Jobs missing billing'],
  ['Complete billed total'],['Known provider subtotal'],['Jobs missing cost'],['Complete provider total'],['Completed share']];
analysis.getRange('C8:C16').values=[['jobs'],['jobs'],['cents'],['jobs'],['cents'],['cents'],['jobs'],['cents'],['share']];
analysis.getRange('B8:B16').formulas=[['=SUM(G20:G28)'],['=SUM(L20:L28)'],['=SUM(I20:I28)'],['=SUM(H20:H28)'],
  ['=IF(B11=0,B10,"n.a.")'],['=SUM(J20:J28)'],['=SUM(K20:K28)'],['=IF(B14=0,B13,"n.a.")'],['=IF(B8=0,"n.a.",B9/B8)']];
analysis.getRange('B8:B15').setNumberFormat('#,##0');
analysis.getRange('B16').setNumberFormat('0.0%');
analysis.getRange('E7:I7').values=[['Plan','Known billed','Missing billing','Known cost','Jobs']];
analysis.getRange('E8:E10').values=[['paid'],['free'],['Unmapped']];
analysis.getRange('F8:I10').formulas=[8,9,10].map(r=>[
  `=SUMIFS($I$20:$I$28,$C$20:$C$28,E${r})`,`=SUMIFS($H$20:$H$28,$C$20:$C$28,E${r})`,
  `=SUMIFS($J$20:$J$28,$C$20:$C$28,E${r})`,`=SUMIFS($G$20:$G$28,$C$20:$C$28,E${r})`]);
analysis.getRange('E12').values=[['Reconciliation items']];analysis.getRange('E12').format.font.bold=true;
analysis.getRange('E13:E16').values=[['Unassigned cost (cents)'],['Unassigned attempts'],['Jobs with date issues'],['Unmapped period jobs']];
analysis.getRange('G13:G16').formulas=[['=SUMIFS(Sources!$J$6:$J$14,Sources!$L$6:$L$14,1)'],
  ['=COUNTIFS(Sources!$L$6:$L$14,1)'],['=COUNTBLANK(Sources!$D$6:$D$14)'],['=SUMIFS($G$20:$G$28,$C$20:$C$28,"Unmapped")']];
analysis.getRange('A18').values=[['Job calculations: one row per prepared job; source tables retain unmatched costs.']];
analysis.getRange('A19:L19').values=[['Job ID','UTC timestamp','Plan','Status','Billed cents','Known cost','In period','Missing bill','Period billed','Period cost','Missing cost','Completed']];
analysis.getRange('A20:L28').formulas=data.jobs.map((_,i)=>{
  const s=i+6,r=i+20;
  const n=`COUNTIFS(Sources!$N$6:$N$8,Sources!B${s})`;
  const plan=`INDEX(Sources!$O$6:$O$8,MATCH(Sources!B${s},Sources!$N$6:$N$8,0))`;
  const attempts=`COUNTIFS(Sources!$I$6:$I$14,A${r})`;
  const valid=`SUMIFS(Sources!$K$6:$K$14,Sources!$I$6:$I$14,A${r})`;
  return [`=Sources!A${s}`,`=IF(ISNUMBER(Sources!D${s}),Sources!D${s},"")`,
    `=IF(${n}=0,"Unmapped",IF(${n}>1,"Duplicate key",IF(${plan}="","Missing plan",${plan})))`,
    `=Sources!E${s}`,`=IF(ISNUMBER(Sources!F${s}),Sources!F${s},"n.a.")`,
    `=SUMIFS(Sources!$J$6:$J$14,Sources!$I$6:$I$14,A${r})`,
    `=IF(ISNUMBER(B${r}),IF(AND(B${r}>=$B$5,B${r}<$E$5),1,0),0)`,
    `=IF(AND(G${r}=1,NOT(ISNUMBER(E${r}))),1,0)`,
    `=IF(AND(G${r}=1,ISNUMBER(E${r})),E${r},0)`,`=IF(G${r}=1,F${r},0)`,
    `=IF(G${r}=1,IF(OR(${attempts}=0,${valid}<>${attempts}),1,0),0)`,
    `=IF(AND(G${r}=1,D${r}="completed"),1,0)`];
});
analysis.getRange('A20:A28').setNumberFormat('0000');
analysis.getRange('B20:B28').setNumberFormat('yyyy-mm-dd hh:mm');
analysis.getRange('E20:L28').setNumberFormat('#,##0');
for(const [sheet,range] of [[analysis,'A7:C7'],[analysis,'E7:I7'],[analysis,'A19:L19'],
                           [sources,'A5:F5'],[sources,'H5:L5'],[sources,'N5:O5']]){
  sheet.getRange(range).format={fill:'#E6EBF3',font:{name:'Arial',size:10,bold:true,color:'#203A5D'},
    horizontalAlignment:'center',verticalAlignment:'center',rowHeight:30,wrapText:true};
}
const analysisWidths=[29,24,12,18,25,15,17,16,19,17,16,15];
const sourceWidths=[14,16,38,24,16,16,3,14,14,15,13,13,3,16,14];
for(const [sheet,widths] of [[analysis,analysisWidths],[sources,sourceWidths]])
  widths.forEach((width,i)=>sheet.getRangeByIndexes(0,i,sheet===analysis?29:16,1).format.columnWidth=width);
analysis.getRange('B8:B16').format.horizontalAlignment='right';
analysis.getRange('F8:I10').format.horizontalAlignment='right';
analysis.getRange('G13:G16').format.horizontalAlignment='right';
analysis.getRange('B11').conditionalFormats.add('cellIs',{operator:'greaterThan',formula:0,format:{fill:'#FFF0D9',font:{color:'#8C4A00'}}});
analysis.getRange('B14').conditionalFormats.add('cellIs',{operator:'greaterThan',formula:0,format:{fill:'#FFF0D9',font:{color:'#8C4A00'}}});
analysis.getRange('G13:G16').conditionalFormats.add('cellIs',{operator:'greaterThan',formula:0,format:{fill:'#FFF0D9',font:{color:'#8C4A00'}}});
const baseline=()=>analysis.getRange('B8:B16').values.flat();
wb.recalculate();
assert.deepEqual(baseline(),[5,4,290,2,'n.a.',110,0,110,0.8]);
const mutations=[];
sources.getRange('F7').values=[[250]];wb.recalculate();assert.equal(baseline()[2],340);mutations.push('Billed amount edit updates subtotal');
sources.getRange('F7').values=[[200]];
sources.getRange('F8').values=[[null]];wb.recalculate();assert.equal(baseline()[3],3);mutations.push('Blank differs from a valid zero');
sources.getRange('F8').values=[[0]];
sources.getRange('F9').values=[[0]];wb.recalculate();assert.equal(baseline()[3],1);assert.equal(baseline()[4],'n.a.');mutations.push('One completed prerequisite leaves other missing input visible');
sources.getRange('F10').values=[[100]];wb.recalculate();assert.equal(baseline()[4],390);mutations.push('All billed amounts enable a complete total');
sources.getRange('F9').values=[[null]];sources.getRange('F10').values=[[null]];
sources.getRange('J7').values=[[null]];wb.recalculate();assert.equal(baseline()[5],100);assert.equal(baseline()[6],1);assert.equal(baseline()[7],'n.a.');mutations.push('Partial missing cost preserves known subtotal and withholds complete cost');
sources.getRange('J7').values=[[10]];
analysis.getRange('E5').values=[[new Date('2026-10-20T00:00:00Z')]];wb.recalculate();assert.equal(baseline()[0],3);assert.equal(baseline()[4],290);assert.equal(baseline()[5],70);mutations.push('Exclusive report boundary changes included jobs');
analysis.getRange('E5').values=[[new Date(data.end)]];
wb.recalculate();assert.deepEqual(baseline(),[5,4,290,2,'n.a.',110,0,110,0.8]);
const inspect=await wb.inspect({kind:'table',range:'Analysis!A7:I16',include:'values,formulas',tableMaxRows:10,tableMaxCols:9});
await fs.writeFile(path.join(qa,'inspection.ndjson'),inspect.ndjson);
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},summary:'Final formula error scan'});
await fs.writeFile(path.join(qa,'error-scan.ndjson'),errors.ndjson);
const file=await SpreadsheetFile.exportXlsx(wb);await file.save(path.join(out,'analysis-practice.xlsx'));
for(const [sheetName,range,name] of [['Analysis','A1:I17','analysis-summary.png'],['Analysis','A18:L28','analysis-detail.png'],['Sources','A1:O15','sources.png']]){
  const preview=await wb.render({sheetName,range,scale:1.5,format:'png'});
  await fs.writeFile(path.join(qa,name),new Uint8Array(await preview.arrayBuffer()));
}
await fs.writeFile(path.join(base,'workbook-validation.json'),JSON.stringify({artifact_formula_checks:'passed',
  baseline_summary:baseline(),mutations,restored_original_inputs:true,native_excel_verification:'See native-excel-validation.json; this builder does not execute Excel',
  workbook:'outputs/p3-analysis/analysis-practice.xlsx',scope:'Artifact Tool recalculation/export; native engine checked separately'},null,2)+'\n');
console.log(JSON.stringify({baseline:baseline(),mutationChecks:mutations.length,exported:true,renderedSheets:2},null,2));
