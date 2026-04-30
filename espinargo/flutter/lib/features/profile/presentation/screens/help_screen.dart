import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../widgets/profile_menu_item.dart';

/// Pantalla de ayuda y FAQ.
class HelpScreen extends StatelessWidget {
  const HelpScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Ayuda'),
        backgroundColor: Colors.transparent,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.packageLight,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              children: [
                const Icon(Icons.support_agent, size: 50, color: AppColors.package),
                const SizedBox(height: 12),
                Text('¿Necesitas ayuda?', style: AppTextStyles.headingSmall),
                const SizedBox(height: 8),
                Text(
                  'Nuestro equipo está disponible 24/7',
                  style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: () {},
                  icon: const Icon(Icons.chat),
                  label: const Text('Chatear'),
                  style: ElevatedButton.styleFrom(backgroundColor: AppColors.package),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          Text('Preguntas frecuentes', style: AppTextStyles.labelLarge),
          const SizedBox(height: 12),
          _buildFaqItem(
            '¿Cómo solicito un viaje?',
            'Abre la app, ingresa tu destino y espera a que un conductor acepte tu solicitud.',
          ),
          _buildFaqItem(
            '¿Cómo me registro como conductor?',
            'Ve a tu perfil > Conductor > Completar registro y sube tus documentos.',
          ),
          _buildFaqItem(
            '¿Qué métodos de pago aceptan?',
            'Aceptamos efectivo, Yape y Plin. Próximamente más opciones.',
          ),
          _buildFaqItem(
            '¿Cómo puedo cancelar un viaje?',
            'Puedes cancelar antes de que el conductor llegue. Se aplicará una penalidad.',
          ),
          _buildFaqItem(
            '¿Cómo funciona el sistema de precios?',
            'Los precios son justos y transparentes. El precio se muestra antes de confirmar.',
          ),
          const SizedBox(height: 24),
          Text('Contacto', style: AppTextStyles.labelLarge),
          const SizedBox(height: 12),
          ProfileMenuItem(
            icon: Icons.email,
            title: 'Correo electrónico',
            subtitle: 'soporte@espinargo.com',
            showArrow: false,
            onTap: () {},
          ),
          ProfileMenuItem(
            icon: Icons.phone,
            title: 'Teléfono',
            subtitle: '+51 984 123 456',
            showArrow: false,
            onTap: () {},
          ),
          ProfileMenuItem(
            icon: Icons.location_on,
            title: 'Oficina',
            subtitle: 'Av. Principal 123, Espinar',
            showArrow: false,
            onTap: () {},
          ),
        ],
      ),
    );
  }

  Widget _buildFaqItem(String question, String answer) {
    return ExpansionTile(
      title: Text(question, style: AppTextStyles.bodyMedium),
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: Text(answer, style: AppTextStyles.bodySmall),
        ),
      ],
    );
  }
}