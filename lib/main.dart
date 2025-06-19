import 'package:flutter/material.dart';
import 'dart:math';
import 'grafico_page.dart';

const double ln10 = 2.302585093;

void main() {
  runApp(const EspectrograficoApp());
}

class EspectrograficoApp extends StatelessWidget {
  const EspectrograficoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'EspectrograficoApp',
      theme: ThemeData.dark().copyWith(
        primaryColor: Colors.indigoAccent,
        scaffoldBackgroundColor: const Color(0xFF121212),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.indigoAccent,
            padding: const EdgeInsets.symmetric(vertical: 16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.grey.shade900,
          labelStyle: const TextStyle(color: Colors.indigoAccent),
          enabledBorder: OutlineInputBorder(
            borderSide: const BorderSide(color: Colors.indigoAccent),
            borderRadius: BorderRadius.circular(10),
          ),
          focusedBorder: OutlineInputBorder(
            borderSide: const BorderSide(color: Colors.indigoAccent, width: 2),
            borderRadius: BorderRadius.circular(10),
          ),
          errorBorder: OutlineInputBorder(
            borderSide: const BorderSide(color: Colors.redAccent),
            borderRadius: BorderRadius.circular(10),
          ),
          focusedErrorBorder: OutlineInputBorder(
            borderSide: const BorderSide(color: Colors.redAccent, width: 2),
            borderRadius: BorderRadius.circular(10),
          ),
        ),
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final List<TextEditingController> fcControllers =
  List.generate(3, (_) => TextEditingController());
  final List<TextEditingController> bwControllers =
  List.generate(3, (_) => TextEditingController());
  final List<TextEditingController> potenciaControllers =
  List.generate(3, (_) => TextEditingController());

  final List<String> unidadesPotencia = List.generate(3, (_) => 'W');

  final TextEditingController temperaturaController = TextEditingController();
  final TextEditingController bwRuidoController = TextEditingController();

  // Función para validar potencia según la unidad
  bool esValorPotenciaValido(String valor, String unidad) {
    final double? v = double.tryParse(valor);
    if (v == null) return false;

    // Para dBm permitimos cualquier valor (incluyendo negativos)
    if (unidad == 'dBm') return true;

    // Para W y mW solo permitimos valores positivos
    return v > 0;
  }

  // Función para validación de frecuencia y ancho de banda (solo valores positivos)
  bool esValorPositivo(String valor) {
    final double? v = double.tryParse(valor);
    return v != null && v > 0;
  }

  @override
  void dispose() {
    for (final c in [
      ...fcControllers,
      ...bwControllers,
      ...potenciaControllers
    ]) {
      c.dispose();
    }
    temperaturaController.dispose();
    bwRuidoController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(100),
        child: AppBar(
          flexibleSpace: Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.indigo, Colors.blueAccent],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
          ),
          title: Row(
            children: const [
              Icon(Icons.signal_cellular_alt, size: 30),
              SizedBox(width: 12),
              Text(
                'Ingreso de Señales',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          centerTitle: false,
          elevation: 8,
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
        child: Column(
          children: [
            // Tarjeta descriptiva
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 0, vertical: 16),
              child: Card(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                color: Colors.indigo.shade700,
                elevation: 6,
                child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const [
                      Text(
                        'Ingreso de Señales',
                        style: TextStyle(
                            fontSize: 28,
                            fontWeight: FontWeight.bold,
                            color: Colors.white),
                      ),
                      SizedBox(height: 8),
                      Text(
                        'Ingresa las frecuencias, potencias y anchos de banda para cada señal para visualizar el espectro.',
                        style: TextStyle(fontSize: 16, color: Colors.white70),
                      ),
                    ],
                  ),
                ),
              ),
            ),

            const Text(
              'Ingrese los datos de las 3 señales:',
              style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w600,
                  color: Colors.indigoAccent),
            ),
            const SizedBox(height: 16),
            for (int i = 0; i < 3; i++)
              Card(
                color: Colors.grey.shade900,
                margin: const EdgeInsets.only(bottom: 20),
                shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                elevation: 8,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Señal ${i + 1}',
                          style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Colors.white)),
                      const SizedBox(height: 12),
                      TextField(
                        controller: fcControllers[i],
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Frecuencia central (MHz)',
                          prefixIcon: Icon(Icons.speed, color: Colors.indigoAccent),
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: bwControllers[i],
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Ancho de banda (MHz)',
                          prefixIcon: Icon(Icons.swap_horiz, color: Colors.indigoAccent),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: potenciaControllers[i],
                              keyboardType: TextInputType.number,
                              decoration: const InputDecoration(
                                labelText: 'Potencia',
                                prefixIcon: Icon(Icons.power, color: Colors.indigoAccent),
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          DropdownButton<String>(
                            value: unidadesPotencia[i],
                            dropdownColor: Colors.grey.shade900,
                            iconEnabledColor: Colors.indigoAccent,
                            items: const [
                              DropdownMenuItem(
                                  value: 'W',
                                  child: Text('W', style: TextStyle(color: Colors.white))),
                              DropdownMenuItem(
                                  value: 'mW',
                                  child: Text('mW', style: TextStyle(color: Colors.white))),
                              DropdownMenuItem(
                                  value: 'dBm',
                                  child: Text('dBm', style: TextStyle(color: Colors.white))),
                            ],
                            onChanged: (value) {
                              setState(() {
                                unidadesPotencia[i] = value!;
                              });
                            },
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            Card(
              color: Colors.grey.shade900,
              shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
              elevation: 8,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    const Text(
                      'Parámetros del ruido térmico:',
                      style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w600,
                          color: Colors.indigoAccent),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: temperaturaController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: 'Temperatura (°K)',
                        prefixIcon: Icon(Icons.thermostat, color: Colors.indigoAccent),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: bwRuidoController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: 'Ancho de banda del ruido (MHz)',
                        prefixIcon: Icon(Icons.blur_on, color: Colors.indigoAccent),
                      ),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton(
                      onPressed: () {
                        try {
                          for (int i = 0; i < 3; i++) {
                            if (!esValorPositivo(fcControllers[i].text)) {
                              throw Exception('La frecuencia central de la Señal ${i + 1} debe ser mayor que cero.');
                            }
                            if (!esValorPositivo(bwControllers[i].text)) {
                              throw Exception('El ancho de banda de la Señal ${i + 1} debe ser mayor que cero.');
                            }
                            if (!esValorPotenciaValido(potenciaControllers[i].text, unidadesPotencia[i])) {
                              throw Exception('La potencia de la Señal ${i + 1}: Para W/mW debe ser mayor que cero, para dBm puede ser cualquier valor.');
                            }
                          }
                          if (!esValorPositivo(temperaturaController.text)) {
                            throw Exception('La temperatura debe ser mayor que cero.');
                          }
                          if (!esValorPositivo(bwRuidoController.text)) {
                            throw Exception('El ancho de banda del ruido debe ser mayor que cero.');
                          }

                          final List<double> fcMHz = fcControllers.map((c) => double.parse(c.text)).toList();
                          final List<double> bwMHz = bwControllers.map((c) => double.parse(c.text)).toList();

                          final double temperatura = double.parse(temperaturaController.text);
                          final double bwRuidoMHz = double.parse(bwRuidoController.text);
                          final double bwRuidoHz = bwRuidoMHz * 1e6;

                          const double k = 1.38e-23;
                          double ruidoDbm = 10 * (log(k * temperatura * bwRuidoHz) / ln10) + 30;

                          // Conversión de potencias a dBm
                          List<double> potDbm = [];
                          for (int i = 0; i < 3; i++) {
                            double valor = double.parse(potenciaControllers[i].text);
                            String unidad = unidadesPotencia[i];

                            if (unidad == 'dBm') {
                              // Si ya está en dBm, usar directamente el valor
                              potDbm.add(valor);
                            } else {
                              // Para W y mW, convertir a dBm
                              double potenciaWatts;
                              if (unidad == 'W') {
                                potenciaWatts = valor;
                              } else { // mW
                                potenciaWatts = valor / 1000;
                              }
                              // Conversión a dBm (valor ya validado como positivo)
                              potDbm.add(10 * (log(potenciaWatts * 1000) / ln10));
                            }
                          }

                          print('Datos a graficar:'); // DEBUG
                          print('Frecuencias: $fcMHz');
                          print('Potencias dBm: $potDbm');
                          print('Ruido dBm: $ruidoDbm');
                          print('Anchos de banda: $bwMHz');

                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => GraficoPage(
                                frecuenciasMHz: fcMHz,
                                potenciasDbm: potDbm,
                                ruidoDbm: ruidoDbm,
                                bwMHz: bwMHz,
                              ),
                            ),
                          );
                        } catch (e) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text(e.toString())),
                          );
                        }
                      },
                      child: const Center(child: Text('Graficar espectro')),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}