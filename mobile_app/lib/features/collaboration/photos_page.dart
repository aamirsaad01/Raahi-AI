import 'package:flutter/material.dart';

class PhotosPage extends StatelessWidget {
  const PhotosPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Photo Album'),
        actions: <Widget>[
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.upload_rounded,
              tooltip: 'Upload',
              onTap: () {},
            ),
          ),
        ],
      ),
      body: GridView.builder(
        padding: const EdgeInsets.all(8),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 3,
          crossAxisSpacing: 4,
          mainAxisSpacing: 4,
        ),
        itemCount: 12,
        itemBuilder: (BuildContext context, int i) {
          return Container(
            color: Colors.grey.shade300,
            child: const Center(child: Icon(Icons.image_rounded)),
          );
        },
      ),
    );
  }
}

class _IconFilledButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  final String? tooltip;

  const _IconFilledButton({required this.icon, required this.onTap, this.tooltip});

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    final Widget btn = Material(
      color: colors.primary,
      shape: const StadiumBorder(),
      child: InkWell(
        customBorder: const StadiumBorder(),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Icon(icon, color: Colors.white),
        ),
      ),
    );
    if (tooltip != null) return Tooltip(message: tooltip!, child: btn);
    return btn;
  }
}

