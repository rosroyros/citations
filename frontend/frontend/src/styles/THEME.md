# Brand Theme Configuration

Last updated: 2025-12-11

## Colors

Use these Tailwind classes in components:

### Primary Color
- `bg-primary` - Primary background (#9333ea)
- `text-primary` - Primary text
- `border-primary` - Primary border
- `hover:bg-primary-dark` - Primary hover state (#7c3aed)
- `bg-primary-light` - Light purple background (rgba(147, 51, 234, 0.1))

### Success/Accent
- `bg-success` - Success background (#10b981)
- `text-success` - Success text (checkmarks, badges)

### Secondary
- `bg-secondary` - Secondary background (#64748b)
- `text-secondary` - Secondary text

### Typography
- `text-heading` - Heading text color (#1f2937)
- `text-body` - Body text color (#6b7280)
- `font-heading` - Heading font family
- `font-body` - Body font family

### Border Radius
- `rounded-card` - Consistent card corner rounding (0.75rem)

## Examples

```jsx
// Card with primary border
<Card className="border-2 border-primary">

// Primary button
<Button className="bg-primary hover:bg-primary-dark">

// Success badge
<div className="bg-success text-white">Best Value</div>

// Typography
<h2 className="font-heading text-heading">Title</h2>
<p className="font-body text-body">Description</p>

// Card example
<Card className="rounded-card border border-gray-200 p-4">
  <CardHeader>
    <CardTitle className="font-heading text-heading">Card Title</CardTitle>
    <CardDescription className="font-body text-body">
      Card description text
    </CardDescription>
  </CardHeader>
  <CardContent>
    <Button className="w-full bg-primary hover:bg-primary-dark">
      Action Button
    </Button>
  </CardContent>
</Card>
```

## Usage Guidelines

1. **Always use semantic class names** - Use `text-primary` instead of hard-coded colors
2. **Consistent spacing** - Use the `rounded-card` class for all card corners
3. **Button hierarchy** - Use primary color for main CTAs, secondary for secondary actions
4. **Success states** - Use success color for checkmarks, completion states, and "Best Value" badges

## Color Values

For reference, here are the actual hex values:
- Primary: #9333ea
- Primary Dark: #7c3aed
- Primary Light: rgba(147, 51, 234, 0.1)
- Secondary: #64748b
- Success: #10b981
- Heading: #1f2937
- Body: #6b7280

## Testing

To verify the theme configuration:
1. Start dev server: `npm run dev`
2. Navigate to: `http://localhost:5176/`
3. The primary purple (#9333ea) should be visible in buttons and UI elements
4. Check that fonts match the clean system font stack