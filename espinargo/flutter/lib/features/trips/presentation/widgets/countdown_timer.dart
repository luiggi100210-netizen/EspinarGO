import 'dart:async';

import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';

/// Widget de cuenta regresiva para las ofertas.
class CountdownTimer extends StatefulWidget {
  final DateTime expiresAt;
  final VoidCallback onExpired;
  final TextStyle? style;

  const CountdownTimer({
    super.key,
    required this.expiresAt,
    required this.onExpired,
    this.style,
  });

  @override
  State<CountdownTimer> createState() => _CountdownTimerState();
}

class _CountdownTimerState extends State<CountdownTimer> {
  late Timer _timer;
  String _timeRemaining = '';

  @override
  void initState() {
    super.initState();
    _updateTime();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) => _updateTime());
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  void _updateTime() {
    final now = DateTime.now();
    final diff = widget.expiresAt.difference(now);

    if (diff.isNegative) {
      _timer.cancel();
      widget.onExpired();
      setState(() => _timeRemaining = 'Expirado');
      return;
    }

    final minutes = diff.inMinutes;
    final seconds = diff.inSeconds % 60;

    setState(() {
      _timeRemaining = '$minutes:${seconds.toString().padLeft(2, '0')}';
    });
  }

  bool get _isUrgent {
    final diff = widget.expiresAt.difference(DateTime.now());
    return diff.inSeconds <= 30;
  }

  @override
  Widget build(BuildContext context) {
    final isExpired = _timeRemaining == 'Expirado';

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          Icons.timer_outlined,
          size: 16,
          color: isExpired ? AppColors.error : (_isUrgent ? AppColors.warning : AppColors.textSecondary),
        ),
        const SizedBox(width: 4),
        Text(
          _timeRemaining,
          style: (widget.style ?? AppTextStyles.labelMedium).copyWith(
            color: isExpired ? AppColors.error : (_isUrgent ? AppColors.warning : AppColors.textSecondary),
            fontWeight: _isUrgent ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ],
    );
  }
}