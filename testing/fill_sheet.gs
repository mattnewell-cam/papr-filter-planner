function fillNetLogs() {
  var ss = SpreadsheetApp.getActive();
  var sh = ss.getSheetByName('V-PF relationship');

  // --- 0-layer (rig) baseline fit, out of the way in N53:O57 -----------------
  sh.getRange('N53').setValue('0-layer (rig) baseline fit:  ln(logPF0) = a + b*ln(V)');
  sh.getRange('N55').setValue('a');
  sh.getRange('N56').setValue('b');
  sh.getRange('N57').setValue('R²');
  sh.getRange('O55').setFormula('=INDEX(LINEST(LN(H49:H52),LN(E49:E52)),1,2)');
  sh.getRange('O56').setFormula('=INDEX(LINEST(LN(H49:H52),LN(E49:E52)),1,1)');
  sh.getRange('O57').setFormula('=RSQ(LN(H49:H52),LN(E49:E52))');

  // --- fill the x's: non-material logs, and net logs -------------------------
  var nonMat = [], net = [];
  for (var r = 54; r <= 65; r++) {
    nonMat.push(['=EXP($O$55+$O$56*LN(E' + r + '))']);
    net.push(['=H' + r + '-I' + r]);
  }
  sh.getRange('I54:I65').setFormulas(nonMat);
  sh.getRange('J54:J65').setFormulas(net);

  // --- plot block: net logs per layer, all 12 samples, split by layer count ---
  sh.getRange('A108').setValue('Plot — net logs per layer, all 12 samples');
  sh.getRange('A109:H109').setValues([[
    'Layers', 'ln(v)', 'ln(net logs/layer)', '', 'ln(v)', '1 layer', '2 layers', '4 layers'
  ]]);

  var rows = [];
  for (var i = 0; i < 12; i++) {
    var src = 54 + i;            // source row in the net-logs block
    var out = 110 + i;           // destination row
    var lay = i < 4 ? 1 : (i < 8 ? 2 : 4);
    var col = lay === 1 ? 5 : (lay === 2 ? 6 : 7);   // offset into F/G/H
    var row = [
      '=A' + src,
      '=LN(E' + src + ')',
      '=LN(K' + src + ')',
      '',
      '=B' + out,
      '', '', ''
    ];
    row[col] = '=$C' + out;
    rows.push(row);
  }
  sh.getRange('A110:H121').setFormulas(rows);

  // --- chart, coloured by layer count ---------------------------------------
  var chart = sh.newChart()
    .setChartType(Charts.ChartType.SCATTER)
    .addRange(sh.getRange('E109:H121'))
    .setPosition(108, 10, 0, 0)
    .setOption('title', 'Net logs per layer vs face velocity, by layer count')
    .setOption('hAxis', {title: 'ln(v)   [v in cm/s]'})
    .setOption('vAxis', {title: 'ln(net logs per layer)'})
    .setOption('useFirstColumnAsDomain', true)
    .setOption('trendlines', {0: {type: 'linear'}, 1: {type: 'linear'}, 2: {type: 'linear'}})
    .setOption('pointSize', 7)
    .setOption('width', 700)
    .setOption('height', 440)
    .build();
  sh.insertChart(chart);
}
