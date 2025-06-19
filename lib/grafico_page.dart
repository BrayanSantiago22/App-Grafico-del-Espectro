import 'dart:math';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

class GraficoPage extends StatelessWidget {
  final List<double> frecuenciasMHz;
  final List<double> potenciasDbm;
  final double ruidoDbm;
  final List<double> bwMHz;

  const GraficoPage({
    super.key,
    required this.frecuenciasMHz,
    required this.potenciasDbm,
    required this.ruidoDbm,
    required this.bwMHz,
  });

  // Generar ruido fluctuante sobre el piso de ruido (puntos en todo el rango)
  List<FlSpot> _generarRuidoAleatorio(double minFreq, double maxFreq, int nPoints, double baseRuido) {
    final random = Random();
    List<FlSpot> ruidoSpots = [];
    double step = (maxFreq - minFreq) / (nPoints - 1);
    for (int i = 0; i < nPoints; i++) {
      double freq = minFreq + i * step;
      double ruidoFluctuado = baseRuido + (random.nextDouble() - 0.5);
      ruidoSpots.add(FlSpot(freq, ruidoFluctuado));
    }
    return ruidoSpots;
  }

  // Calcular rango de frecuencias para cada senal
  List<List<double>> _calcularRangoFrecuencias() {
    List<List<double>> rangos = [];
    for (int i = 0; i < frecuenciasMHz.length; i++) {
      double fc = frecuenciasMHz[i];
      double bw = bwMHz[i];
      rangos.add([fc - bw / 2, fc + bw / 2]);
    }
    return rangos;
  }

  // Generar puntos para cada senal, formando un escalon rectangular
  List<FlSpot> _generarPuntosSenal(double minF, double maxF, double potencia) {
    return [
      FlSpot(minF, 0),
      FlSpot(minF, potencia),
      FlSpot(maxF, potencia),
      FlSpot(maxF, 0),
    ];
  }

  // Calcular interferencias como diferencia minima absoluta de potencias entre señales
  double _calcularInterferencia() {
    double minDiff = double.infinity;
    for (int i = 0; i < potenciasDbm.length; i++) {
      for (int j = i + 1; j < potenciasDbm.length; j++) {
        double diff = (potenciasDbm[i] - potenciasDbm[j]).abs();
        if (diff < minDiff) minDiff = diff;
      }
    }
    return minDiff.isFinite ? minDiff : 0;
  }

  @override
  Widget build(BuildContext context) {
    final rangos = _calcularRangoFrecuencias();
    final List<LineChartBarData> lineBars = [];

    // Colores para señales
    final List<Color> signalColors = [Colors.blue, Colors.green, Colors.orange];

    // Señales con areas y sin puntos por defecto
    for (int i = 0; i < rangos.length; i++) {
      final spots = _generarPuntosSenal(rangos[i][0], rangos[i][1], potenciasDbm[i]);
      lineBars.add(
        LineChartBarData(
          spots: spots,
          isCurved: false,
          color: signalColors[i % signalColors.length],
          barWidth: 3,
          belowBarData: BarAreaData(
            show: true,
            color: signalColors[i % signalColors.length].withOpacity(0.4),
          ),
          dotData: FlDotData(show: false),
        ),
      );
      // Punto central destacado para la señal
      lineBars.add(
        LineChartBarData(
          spots: [FlSpot(frecuenciasMHz[i], potenciasDbm[i])],
          isCurved: false,
          color: signalColors[i % signalColors.length],
          barWidth: 6,
          dotData: FlDotData(
            show: true,
            getDotPainter: (spot, percent, barData, index) => FlDotCirclePainter(
              radius: 6,
              color: signalColors[i % signalColors.length],
              strokeWidth: 0,
              strokeColor: Colors.transparent,
            ),
          ),
          belowBarData: BarAreaData(show: false),
        ),
      );
    }

    double minFreqTotal = rangos.map((r) => r[0]).reduce(min);
    double maxFreqTotal = rangos.map((r) => r[1]).reduce(max);

    final ruidoSpots = _generarRuidoAleatorio(minFreqTotal, maxFreqTotal, 50, ruidoDbm);

    lineBars.add(
      LineChartBarData(
        spots: ruidoSpots,
        color: Colors.red,
        isCurved: false,
        barWidth: 2,
        dotData: FlDotData(show: false),
        belowBarData: BarAreaData(
          show: true,
          color: Colors.red.withOpacity(0.15),
        ),
      ),
    );

    double minY = (ruidoDbm - 20).clamp(-150, 0);
    double maxY = (potenciasDbm.reduce(max) + 10).clamp(-150, 50);

    List<double> snr = potenciasDbm.map((p) => p - ruidoDbm).toList();
    double interferencia = _calcularInterferencia();

    return Scaffold(
      appBar: AppBar(title: const Text('Espectro de Senales')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Expanded(
              child: LineChart(
                LineChartData(
                  minY: minY,
                  maxY: maxY,
                  minX: minFreqTotal - 5,
                  maxX: maxFreqTotal + 5,
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: true,
                    verticalInterval: (maxFreqTotal - minFreqTotal) / 6,
                    horizontalInterval: 10,
                    getDrawingHorizontalLine: (value) =>
                        FlLine(color: Colors.grey.shade700, strokeWidth: 1),
                    getDrawingVerticalLine: (value) =>
                        FlLine(color: Colors.grey.shade700, strokeWidth: 1),
                  ),
                  titlesData: FlTitlesData(
                    bottomTitles: AxisTitles(
                      axisNameWidget: const Text(
                        'Frecuencia (MHz)',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      sideTitles: SideTitles(
                        showTitles: true,
                        interval: (maxFreqTotal - minFreqTotal) / 6,
                        getTitlesWidget: (value, meta) {
                          return Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Text(
                              value.toStringAsFixed(0),
                              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                            ),
                          );
                        },
                      ),
                    ),
                    leftTitles: AxisTitles(
                      axisNameWidget: const Text(
                        'Potencia (dBm)',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      sideTitles: SideTitles(
                        showTitles: true,
                        interval: 10,
                        getTitlesWidget: (value, meta) {
                          return Text(
                            value.toStringAsFixed(0),
                            style: const TextStyle(color: Colors.white),
                          );
                        },
                      ),
                    ),
                  ),
                  lineBarsData: lineBars,
                  borderData: FlBorderData(
                    show: true,
                    border: Border.all(color: Colors.grey.shade600),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text('SNR por senal:', style: Theme.of(context).textTheme.titleMedium?.copyWith(color: Colors.white)),
            const SizedBox(height: 8),
            for (int i = 0; i < snr.length; i++)
              Text('Senal ${i + 1}: ${snr[i].toStringAsFixed(2)} dB', style: const TextStyle(color: Colors.white)),
            const SizedBox(height: 16),
            Text('Nivel de ruido: ${ruidoDbm.toStringAsFixed(2)} dBm', style: const TextStyle(color: Colors.white)),
            const SizedBox(height: 16),
            Text('Interferencia minima entre senales: ${interferencia.toStringAsFixed(2)} dB', style: const TextStyle(color: Colors.white)),
            const SizedBox(height: 16),
            Text('Rango de frecuencias de cada senal (MHz):', style: const TextStyle(color: Colors.white)),
            for (int i = 0; i < rangos.length; i++)
              Text(
                'Senal ${i + 1}: ${rangos[i][0].toStringAsFixed(2)} - ${rangos[i][1].toStringAsFixed(2)}',
                style: const TextStyle(color: Colors.white),
              ),
          ],
        ),
      ),
    );
  }
}